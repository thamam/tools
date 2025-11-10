"""CLI entry point for claude-seed command."""

import click
import sys
import os


# Exit codes per contracts/cli-commands.md
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_SYSTEM_ERROR = 2
EXIT_CONFLICT = 3
EXIT_VALIDATION_ERROR = 4


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Claude Code Project Seeder - Initialize repositories with registry items.

    This tool helps you set up Claude Code repositories by selecting and
    installing sub-agents, commands, and MCP servers from a private registry.

    Examples:
        claude-seed init                    # Interactive initialization
        claude-seed init --filter research  # Filter by tag
        claude-seed install                 # Install from lock file
        claude-seed list                    # List available items
    """
    pass


@cli.command()
@click.option(
    "--filter",
    "-f",
    multiple=True,
    help="Filter items by tag (can be used multiple times)"
)
@click.option(
    "--force",
    is_flag=True,
    help="Allow overwrites and ignore conflicts"
)
@click.option(
    "--output",
    "-o",
    default=".claude",
    help="Output directory for Claude Code files (default: .claude)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without modifying files"
)
@click.option(
    "--registry-path",
    envvar="CLAUDE_REGISTRY_PATH",
    default=os.path.expanduser("~/.claude-registry"),
    help="Path to registry (default: ~/.claude-registry or $CLAUDE_REGISTRY_PATH)"
)
def init(filter, force, output, dry_run, registry_path):
    """Initialize a new repository with selected registry items.

    Interactive multi-select UI for choosing sub-agents, commands, and
    MCP servers from the registry. Automatically resolves dependencies
    and detects conflicts.

    Examples:
        claude-seed init
        claude-seed init --filter research --filter prod-safe
        claude-seed init --dry-run
        claude-seed init --force --output .config/claude
    """
    from pathlib import Path
    import json
    from src.registry.loader import RegistryLoader, RegistryLoadError
    from src.selection.filter import ItemFilter
    from src.selection.prompter import InteractivePrompter, SelectionCancelled
    from src.selection.models import Selection
    from src.registry.resolver import DependencyResolver, DependencyError, CircularDependencyError
    from src.operations.copier import FileCopier, CopyError
    from src.operations.merger import JSONMerger, MergeError
    from src.operations.generator import EnvExampleGenerator, READMEGenerator, GeneratorError
    from src.operations.lockfile import LockFile, LockItem
    from src.validation.integrity import atomic_operation, FileOperation, AtomicOperationError
    from src.validation.schema import MCPSchemaValidator, SchemaValidationError

    click.echo("Initializing Claude Code repository...")
    click.echo(f"Registry: {registry_path}")
    click.echo(f"Output: {output}")

    if dry_run:
        click.echo("\n[DRY RUN] No files will be modified\n")

    try:
        # === SELECTION WORKFLOW ===

        # 1. Load registry
        click.echo("Loading registry...")
        loader = RegistryLoader(registry_path)
        all_items = loader.load_all()

        if not all_items:
            click.echo("Error: No items found in registry", err=True)
            sys.exit(EXIT_USER_ERROR)

        click.echo(f"  Found {len(all_items)} items")

        # 2. Filter by tags if specified
        filtered_items = all_items
        if filter:
            click.echo(f"Applying filters: {', '.join(filter)}")
            filtered_items = ItemFilter.by_tags(filtered_items, list(filter))
            click.echo(f"  {len(filtered_items)} items match filters")

        if not filtered_items:
            click.echo("Error: No items match the specified filters", err=True)
            sys.exit(EXIT_USER_ERROR)

        # 3. Interactive selection
        click.echo("\nSelect items to install:")
        try:
            selected_items = InteractivePrompter.select_items(filtered_items)
        except SelectionCancelled:
            click.echo("\nSelection cancelled")
            sys.exit(EXIT_SUCCESS)

        if not selected_items:
            click.echo("\nNo items selected - nothing to do")
            sys.exit(EXIT_SUCCESS)

        # 4. Resolve dependencies
        click.echo("\nResolving dependencies...")
        try:
            resolved_items = DependencyResolver.resolve_dependencies(
                selected_items, all_items
            )
        except CircularDependencyError as e:
            click.echo(f"\nError: {e}", err=True)
            sys.exit(EXIT_VALIDATION_ERROR)
        except DependencyError as e:
            click.echo(f"\nError: {e}", err=True)
            sys.exit(EXIT_USER_ERROR)

        # Separate selected from dependencies
        selected_names = {item.name for item in selected_items}
        dep_items = [item for item in resolved_items if item.name not in selected_names]

        # Display summary
        InteractivePrompter.display_summary(selected_items, dep_items)

        # Collect all environment variables
        required_env_vars = []
        optional_env_vars = []
        for item in resolved_items:
            required_env_vars.extend(item.get_required_env_vars())
            optional_env_vars.extend(item.get_optional_env_vars())

        if required_env_vars or optional_env_vars:
            InteractivePrompter.display_env_vars(required_env_vars, optional_env_vars)

        # 5. Detect conflicts
        click.echo("Detecting conflicts...")
        mcp_items = [item for item in resolved_items if item.mcp_fragment]
        conflicts = []

        if mcp_items:
            mcp_fragments = {
                item.name: item.mcp_fragment
                for item in mcp_items
            }
            _, conflicts = JSONMerger.merge_with_item_names(
                mcp_fragments, detect_conflicts=True
            )

        if conflicts:
            InteractivePrompter.display_conflicts(conflicts)

            if not force:
                click.echo("Error: Conflicts detected. Use --force to override.", err=True)
                sys.exit(EXIT_CONFLICT)
            else:
                click.echo("⚠️  Proceeding with --force (conflicts will be overwritten)")

        # === DRY RUN MODE ===
        if dry_run:
            click.echo("\n" + "=" * 60)
            click.echo("DRY RUN PREVIEW")
            click.echo("=" * 60)

            # Preview file operations
            operations = FileCopier.preview_copy_operations(
                resolved_items, Path(registry_path), Path(output)
            )

            click.echo(f"\nPlanned file operations ({len(operations)}):")
            for op in operations:
                click.echo(f"  CREATE {op['dest']} ({op['size']})")

            # Preview .mcp.json
            if mcp_items:
                click.echo("\nMCP servers to configure:")
                for item in mcp_items:
                    click.echo(f"  - {item.name}")

            # Preview .env.example
            if required_env_vars or optional_env_vars:
                click.echo("\nEnvironment variables:")
                click.echo(f"  - Required: {len(required_env_vars)}")
                click.echo(f"  - Optional: {len(optional_env_vars)}")

            # Total size
            total_size = FileCopier.get_total_size(resolved_items, Path(registry_path))
            click.echo(f"\nTotal size: {FileCopier.format_size(total_size)}")

            click.echo("\n" + "=" * 60)
            sys.exit(EXIT_SUCCESS if not conflicts else EXIT_CONFLICT)

        # === INSTALLATION WORKFLOW ===

        click.echo("\nInstalling...")

        # Check for existing .claude directory
        output_path = Path(output)
        if output_path.exists() and not force:
            click.echo(f"Error: Directory '{output}' already exists. Use --force to overwrite.", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)

        # Use atomic operation for installation
        try:
            with atomic_operation(output) as temp_dir:
                # Copy files
                click.echo(f"  Copying files to {output}/...")
                FileCopier.copy_all_items(
                    resolved_items, Path(registry_path), temp_dir
                )

                # Merge and write .mcp.json
                if mcp_items:
                    click.echo("  Generating .mcp.json...")
                    merged_mcp, _ = JSONMerger.merge_mcp_fragments(
                        mcp_fragments, detect_conflicts=False
                    )

                    # Validate merged config
                    validator = MCPSchemaValidator()
                    is_valid, errors = validator.validate(merged_mcp)
                    if not is_valid:
                        raise SchemaValidationError(
                            f"Invalid MCP configuration: {'; '.join(errors)}"
                        )

                    # Write with deterministic formatting
                    mcp_path = Path(".mcp.json")
                    FileOperation.write_json(mcp_path, merged_mcp, sort_keys=True)

                # Generate .env.example
                if required_env_vars or optional_env_vars:
                    click.echo("  Generating .env.example...")
                    env_path = Path(".env.example")
                    EnvExampleGenerator.generate(resolved_items, env_path)

                # Generate lock file
                click.echo("  Generating .claude.lock.json...")
                lock_file = LockFile.create_new(str(Path(registry_path).resolve()))

                for item in resolved_items:
                    file_hashes = {}
                    for dest_path in item.files.keys():
                        full_path = temp_dir / dest_path
                        if full_path.exists():
                            file_hashes[dest_path] = FileOperation.compute_sha256(full_path)

                    lock_item = LockItem(
                        type=item.type,
                        version=item.version,
                        files=file_hashes
                    )
                    lock_file.add_item(item.name, lock_item)

                lock_path = Path(".claude.lock.json")
                FileOperation.write_json(lock_path, lock_file.to_dict(), sort_keys=True)

        except AtomicOperationError as e:
            click.echo(f"\nError during installation: {e}", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)
        except (CopyError, MergeError, GeneratorError, SchemaValidationError) as e:
            click.echo(f"\nError: {e}", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)

        # Success!
        click.echo("\n✓ Installation complete!")
        click.echo("\nFiles created:")
        click.echo(f"  - {output}/")
        if mcp_items:
            click.echo("  - .mcp.json")
        if required_env_vars or optional_env_vars:
            click.echo("  - .env.example")
        click.echo("  - .claude.lock.json")

        click.echo(f"\nInstalled {len(resolved_items)} items:")
        for item in resolved_items:
            prefix = "  ✓" if item in selected_items else "  +"
            click.echo(f"{prefix} {item.name} v{item.version}")

        if required_env_vars:
            click.echo(f"\n⚠️  Remember to create .env and set {len(required_env_vars)} required variable(s)")

        sys.exit(EXIT_SUCCESS)

    except RegistryLoadError as e:
        click.echo(f"Error loading registry: {e}", err=True)
        sys.exit(EXIT_SYSTEM_ERROR)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(EXIT_SYSTEM_ERROR)


@cli.command()
@click.option(
    "--lock-file",
    default=".claude.lock.json",
    help="Path to lock file (default: .claude.lock.json)"
)
@click.option(
    "--verify",
    is_flag=True,
    help="Verify file hashes after installation"
)
@click.option(
    "--registry-path",
    envvar="CLAUDE_REGISTRY_PATH",
    default=os.path.expanduser("~/.claude-registry"),
    help="Path to registry (default: ~/.claude-registry or $CLAUDE_REGISTRY_PATH)"
)
def install(lock_file, verify, registry_path):
    """Install items from lock file for reproducible setup.

    Reads the lock file and installs exact versions of items without
    user interaction. Optionally verifies file hashes for integrity.

    Examples:
        claude-seed install
        claude-seed install --verify
        claude-seed install --lock-file custom-lock.json
    """
    from pathlib import Path
    from src.operations.lockfile import LockFile
    from src.registry.loader import RegistryLoader, RegistryLoadError
    from src.operations.copier import FileCopier, CopyError
    from src.operations.merger import JSONMerger, MergeError
    from src.operations.generator import EnvExampleGenerator, GeneratorError
    from src.validation.integrity import atomic_operation, FileOperation, AtomicOperationError
    from src.validation.schema import MCPSchemaValidator, SchemaValidationError

    click.echo(f"Installing from lock file: {lock_file}")
    click.echo(f"Registry: {registry_path}")

    if verify:
        click.echo("Hash verification: enabled\n")

    try:
        # === READ LOCK FILE ===

        lock_path = Path(lock_file)
        if not lock_path.exists():
            click.echo(f"Error: Lock file not found: {lock_file}", err=True)
            click.echo("\nTo create a lock file, run: claude-seed init", err=True)
            sys.exit(EXIT_USER_ERROR)

        click.echo("Reading lock file...")
        try:
            lock_data = FileOperation.read_json(lock_path)
            lock = LockFile.from_dict(lock_data)
        except Exception as e:
            click.echo(f"Error: Invalid lock file: {e}", err=True)
            sys.exit(EXIT_VALIDATION_ERROR)

        click.echo(f"  Lock file version: {lock.version}")
        click.echo(f"  Generated: {lock.generated}")
        click.echo(f"  Registry: {lock.registry_path}")
        click.echo(f"  Items: {len(lock.items)}")

        # === VERIFY REGISTRY ===

        click.echo("\nVerifying registry...")
        registry_path_obj = Path(registry_path)

        # Check if registry path matches lock file
        if str(registry_path_obj.resolve()) != str(Path(lock.registry_path).resolve()):
            click.echo(f"⚠️  Warning: Registry path mismatch")
            click.echo(f"  Lock file expects: {lock.registry_path}")
            click.echo(f"  Using: {registry_path}")
            if not click.confirm("Continue anyway?", default=False):
                sys.exit(EXIT_USER_ERROR)

        # Load registry
        try:
            loader = RegistryLoader(registry_path)
        except RegistryLoadError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)

        # === LOAD AND VERIFY ITEMS ===

        click.echo("\nLoading items from registry...")
        items_to_install = []
        version_mismatches = []

        for item_name, lock_item in lock.items.items():
            # Load item from registry
            try:
                item = loader.find_item(item_name)
                if not item:
                    click.echo(f"Error: Item '{item_name}' not found in registry", err=True)
                    sys.exit(EXIT_USER_ERROR)

                # Check version match
                if item.version != lock_item.version:
                    version_mismatches.append({
                        'name': item_name,
                        'lock_version': lock_item.version,
                        'registry_version': item.version
                    })

                items_to_install.append(item)

            except Exception as e:
                click.echo(f"Error loading '{item_name}': {e}", err=True)
                sys.exit(EXIT_SYSTEM_ERROR)

        # Handle version mismatches
        if version_mismatches:
            click.echo("\n⚠️  Version mismatches detected:")
            for mismatch in version_mismatches:
                click.echo(f"  - {mismatch['name']}: lock={mismatch['lock_version']}, registry={mismatch['registry_version']}")

            click.echo("\nOptions:")
            click.echo("  1. Update registry to match lock file versions")
            click.echo("  2. Regenerate lock file with current registry versions (claude-seed init)")
            click.echo("  3. Continue with registry versions (not recommended)")

            if not click.confirm("\nContinue with registry versions?", default=False):
                sys.exit(EXIT_USER_ERROR)

        click.echo(f"  Loaded {len(items_to_install)} items")

        # === INSTALLATION ===

        click.echo("\nInstalling...")

        # Check for existing .claude directory
        output_path = Path(".claude")
        if output_path.exists():
            click.echo("⚠️  Warning: .claude directory already exists")
            if not click.confirm("Overwrite?", default=False):
                sys.exit(EXIT_USER_ERROR)

        # Use atomic operation for installation
        try:
            with atomic_operation(".claude") as temp_dir:
                # Copy files
                click.echo("  Copying files...")
                FileCopier.copy_all_items(
                    items_to_install, Path(registry_path), temp_dir
                )

                # Merge and write .mcp.json if MCP items present
                mcp_items = [item for item in items_to_install if item.mcp_fragment]
                if mcp_items:
                    click.echo("  Generating .mcp.json...")
                    mcp_fragments = {
                        item.name: item.mcp_fragment
                        for item in mcp_items
                    }
                    merged_mcp, _ = JSONMerger.merge_mcp_fragments(
                        mcp_fragments, detect_conflicts=False
                    )

                    # Validate merged config
                    validator = MCPSchemaValidator()
                    is_valid, errors = validator.validate(merged_mcp)
                    if not is_valid:
                        raise SchemaValidationError(
                            f"Invalid MCP configuration: {'; '.join(errors)}"
                        )

                    # Write with deterministic formatting
                    mcp_path = Path(".mcp.json")
                    FileOperation.write_json(mcp_path, merged_mcp, sort_keys=True)

                # Generate .env.example if env vars present
                env_vars_present = any(item.env_vars for item in items_to_install)
                if env_vars_present:
                    click.echo("  Generating .env.example...")
                    env_path = Path(".env.example")
                    EnvExampleGenerator.generate(items_to_install, env_path)

        except AtomicOperationError as e:
            click.echo(f"\nError during installation: {e}", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)
        except (CopyError, MergeError, GeneratorError, SchemaValidationError) as e:
            click.echo(f"\nError: {e}", err=True)
            sys.exit(EXIT_SYSTEM_ERROR)

        # === HASH VERIFICATION ===

        if verify:
            click.echo("\nVerifying file hashes...")
            verification_failed = []

            install_root = Path(".claude")  # Install directory for verification
            for item_name, lock_item in lock.items.items():
                for file_path, expected_hash in lock_item.files.items():
                    full_path = install_root / file_path
                    if not full_path.exists():
                        verification_failed.append(f"{file_path}: file not found")
                        continue

                    actual_hash = FileOperation.compute_sha256(full_path)
                    if actual_hash != expected_hash:
                        verification_failed.append(
                            f"{file_path}: hash mismatch (expected {expected_hash[:16]}..., got {actual_hash[:16]}...)"
                        )

            if verification_failed:
                click.echo("\n❌ Hash verification failed:")
                for error in verification_failed:
                    click.echo(f"  - {error}")
                click.echo("\nFiles may have been tampered with or registry has changed.")
                sys.exit(EXIT_VALIDATION_ERROR)
            else:
                click.echo("  ✓ All file hashes verified")

        # Success!
        click.echo("\n✓ Installation complete!")
        click.echo(f"\nInstalled {len(items_to_install)} items:")
        for item in items_to_install:
            click.echo(f"  ✓ {item.name} v{item.version}")

        required_env_vars = sum(len(item.get_required_env_vars()) for item in items_to_install)
        if required_env_vars > 0:
            click.echo(f"\n⚠️  Remember to create .env and set {required_env_vars} required variable(s)")

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(EXIT_SYSTEM_ERROR)


@cli.command()
@click.option(
    "--filter",
    "-f",
    multiple=True,
    help="Filter items by tag"
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["subagent", "command", "mcp"], case_sensitive=False),
    help="Filter by item type"
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON instead of table"
)
@click.option(
    "--registry-path",
    envvar="CLAUDE_REGISTRY_PATH",
    default=os.path.expanduser("~/.claude-registry"),
    help="Path to registry (default: ~/.claude-registry or $CLAUDE_REGISTRY_PATH)"
)
def list(filter, type, output_json, registry_path):
    """List available items in the registry.

    Display all sub-agents, commands, and MCP servers available for
    installation. Can be filtered by tags or item type.

    Examples:
        claude-seed list
        claude-seed list --filter research
        claude-seed list --type mcp
        claude-seed list --json
    """
    import json
    from pathlib import Path
    from src.registry.loader import RegistryLoader, RegistryLoadError
    from src.selection.filter import ItemFilter
    from src.registry.models import ItemType

    try:
        # Load registry
        loader = RegistryLoader(registry_path)
        items = loader.load_all()

        if not items:
            click.echo("No items found in registry", err=True)
            sys.exit(EXIT_SUCCESS)

        # Apply filters
        if filter:
            items = ItemFilter.by_tags(items, list(filter))

        if type:
            item_type = ItemType(type)
            items = ItemFilter.by_type(items, item_type)

        if not items:
            click.echo("No items match the specified filters")
            sys.exit(EXIT_SUCCESS)

        # Sort by type then name
        items = ItemFilter.sort_by_type(items)

        # Output as JSON
        if output_json:
            items_data = []
            for item in items:
                items_data.append({
                    'name': item.name,
                    'version': item.version,
                    'type': item.type.value,
                    'category': item.category,
                    'tags': item.tags,
                    'description': item.description,
                    'dependencies': item.dependencies,
                    'env_vars': [
                        {
                            'name': env.name,
                            'description': env.description,
                            'required': env.required,
                            'default': env.default
                        }
                        for env in item.env_vars
                    ]
                })

            output = {
                'registry': registry_path,
                'count': len(items),
                'items': items_data
            }
            click.echo(json.dumps(output, indent=2, sort_keys=True))
            sys.exit(EXIT_SUCCESS)

        # Output as table
        click.echo(f"\nRegistry: {registry_path}")
        if filter:
            click.echo(f"Filters: {', '.join(filter)}")
        if type:
            click.echo(f"Type: {type}")

        click.echo(f"\nFound {len(items)} item(s)\n")

        # Calculate column widths
        max_name = max(len(item.name) for item in items)
        max_version = max(len(item.version) for item in items)
        max_type = max(len(item.type.value) for item in items)

        # Ensure minimum widths
        max_name = max(max_name, 10)
        max_version = max(max_version, 7)
        max_type = max(max_type, 8)

        # Table header
        header = f"{'NAME':<{max_name}}  {'VERSION':<{max_version}}  {'TYPE':<{max_type}}  DESCRIPTION"
        separator = "=" * len(header)

        click.echo(separator)
        click.echo(header)
        click.echo(separator)

        # Table rows
        for item in items:
            # Truncate description if too long
            desc = item.description
            max_desc_len = 60
            if len(desc) > max_desc_len:
                desc = desc[:max_desc_len-3] + "..."

            row = f"{item.name:<{max_name}}  {item.version:<{max_version}}  {item.type.value:<{max_type}}  {desc}"
            click.echo(row)

        click.echo(separator)

        # Summary by type
        type_counts = {}
        for item in items:
            type_counts[item.type.value] = type_counts.get(item.type.value, 0) + 1

        click.echo("\nSummary:")
        for item_type, count in sorted(type_counts.items()):
            click.echo(f"  {item_type}: {count}")

        sys.exit(EXIT_SUCCESS)

    except RegistryLoadError as e:
        click.echo(f"Error loading registry: {e}", err=True)
        sys.exit(EXIT_SYSTEM_ERROR)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(EXIT_SYSTEM_ERROR)


def main():
    """Entry point for CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_SYSTEM_ERROR)


if __name__ == "__main__":
    main()
