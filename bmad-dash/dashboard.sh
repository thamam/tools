#!/bin/bash
# BMAD Dashboard Launcher
# Choose between table view and executive dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Parse arguments
VIEW="executive"  # Default to executive view
REPOS=()
SUMMARY=""
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --view)
            VIEW="$2"
            shift 2
            ;;
        --repos)
            shift
            while [[ $# -gt 0 ]] && [[ ! "$1" =~ ^-- ]] && [[ "$1" != "check" ]]; do
                REPOS+=("$1")
                shift
            done
            ;;
        --summary)
            SUMMARY="--summary"
            shift
            ;;
        check)
            COMMAND="check"
            shift
            ;;
        --help|-h)
            echo "BMAD Dashboard Launcher"
            echo ""
            echo "Usage: $0 [OPTIONS] [COMMAND]"
            echo ""
            echo "Options:"
            echo "  --view <type>       View type: executive (default) or table"
            echo "  --repos <paths>     Repository paths (required)"
            echo "  --summary           Print summary and exit"
            echo ""
            echo "Commands:"
            echo "  check               Run health check and output JSON"
            echo ""
            echo "Examples:"
            echo "  $0 --repos ~/project                    # Executive dashboard"
            echo "  $0 --view table --repos ~/project       # Simple table view"
            echo "  $0 --repos ~/project --summary          # Print summary"
            echo "  $0 check --repos ~/project              # Health check JSON"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if repos are provided
if [ ${#REPOS[@]} -eq 0 ]; then
    echo "Error: --repos is required"
    echo "Use --help for usage information"
    exit 1
fi

# Build repos argument
REPOS_ARG="--repos ${REPOS[@]}"

# Launch appropriate view
if [ "$VIEW" = "executive" ]; then
    python "$SCRIPT_DIR/bmad_dash_enhanced.py" $REPOS_ARG $SUMMARY $COMMAND
elif [ "$VIEW" = "table" ]; then
    python "$SCRIPT_DIR/bmad_dash.py" $REPOS_ARG $SUMMARY $COMMAND
else
    echo "Error: Unknown view type: $VIEW"
    echo "Use 'executive' or 'table'"
    exit 1
fi
