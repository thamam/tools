#!/bin/bash

# Enhanced trip download script
# Usage: download_trip.sh [OPTIONS] TRIP_ID [TRIP_ID...]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Default values
OUTPUT_DIR="."
REMOVE_HEAVY_DIRS=false
VERBOSE=false
QUIET=false
S3_BUCKET="trips-backup"
S3_PREFIX="trips"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    if [[ "$QUIET" == false ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [[ "$QUIET" == false ]]; then
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    fi
}

log_warning() {
    if [[ "$QUIET" == false ]]; then
        echo -e "${YELLOW}[WARNING]${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

show_help() {
    cat << EOF
Enhanced Trip Download Script

USAGE:
    $(basename "$0") [OPTIONS] TRIP_ID [TRIP_ID...]

DESCRIPTION:
    Downloads and extracts trip data from AWS S3 based on trip IDs.
    Trip IDs should be in format: YYYY-MM-DDTHH_MM_SS

OPTIONS:
    -h, --help              Show this help message
    -o, --output-dir DIR    Specify output directory (default: current directory)
    -r, --remove-heavy      Remove 3d_images and lidar_images directories after extraction
    -v, --verbose           Enable verbose output
    -q, --quiet             Suppress non-error output
    -b, --bucket BUCKET     S3 bucket name (default: trips-backup)
    -p, --prefix PREFIX     S3 prefix path (default: trips)
    --dry-run              Show what would be downloaded without actually doing it

EXAMPLES:
    # Basic usage
    $(basename "$0") 2025-07-15T12_06_02
    
    # Download to specific directory and remove heavy directories
    $(basename "$0") -o /tmp/trips -r 2025-07-15T12_06_02 2025-07-14T13_08_09
    
    # Verbose mode with multiple trips
    $(basename "$0") --verbose --remove-heavy 2025-07-15T12_06_02
    
    # Quiet mode (only errors shown)
    $(basename "$0") -q --remove-heavy 2025-07-15T12_06_02
    
    # Preview what would be downloaded without actually doing it
    $(basename "$0") --dry-run 2025-07-15T12_06_02 2025-07-14T13_08_09
    
    # Custom S3 bucket and prefix
    $(basename "$0") -b my-bucket -p custom/path 2025-07-15T12_06_02
    
    # Combine multiple options
    $(basename "$0") -o /data/trips -r -v --dry-run 2025-07-15T12_06_02

EXIT CODES:
    0    Success
    1    General error
    2    Invalid arguments
    3    AWS CLI error
    4    File operation error
EOF
}

validate_trip_id() {
    local trip_id="$1"
    
    # Check format: YYYY-MM-DDTHH_MM_SS
    if [[ ! "$trip_id" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}_[0-9]{2}_[0-9]{2}$ ]]; then
        log_error "Invalid trip ID format: $trip_id"
        log_error "Expected format: YYYY-MM-DDTHH_MM_SS (e.g., 2025-07-15T12_06_02)"
        return 1
    fi
    
    # Extract and validate date components
    local trip_date=$(echo "$trip_id" | cut -d'T' -f 1)
    local trip_year=$(echo "$trip_date" | cut -d'-' -f 1)
    local trip_month=$(echo "$trip_date" | cut -d'-' -f 2)
    local trip_day=$(echo "$trip_date" | cut -d'-' -f 3)
    
    # Basic date validation
    if [[ "$trip_year" -lt 2020 || "$trip_year" -gt 2030 ]]; then
        log_error "Invalid year in trip ID: $trip_year"
        return 1
    fi
    
    if [[ "$trip_month" -lt 1 || "$trip_month" -gt 12 ]]; then
        log_error "Invalid month in trip ID: $trip_month"
        return 1
    fi
    
    if [[ "$trip_day" -lt 1 || "$trip_day" -gt 31 ]]; then
        log_error "Invalid day in trip ID: $trip_day"
        return 1
    fi
    
    return 0
}

check_dependencies() {
    log_verbose "Checking dependencies..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        return 1
    fi
    
    if ! command -v tar &> /dev/null; then
        log_error "tar command not found."
        return 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid."
        return 1
    fi
    
    log_verbose "All dependencies satisfied."
    return 0
}

remove_heavy_directories() {
    local trip_dir="$1"
    
    log_verbose "Checking for heavy directories in $trip_dir..."
    
    for heavy_dir in "3d_images" "lidar_images"; do
        local dir_path="$trip_dir/$heavy_dir"
        if [[ -d "$dir_path" ]]; then
            local size=$(du -sh "$dir_path" 2>/dev/null | cut -f1 || echo "unknown")
            log_info "Removing $heavy_dir directory (size: $size)..."
            rm -rf "$dir_path"
            log_success "Removed $heavy_dir directory"
        else
            log_verbose "$heavy_dir directory not found in $trip_dir"
        fi
    done
}

download_trip() {
    local trip_id="$1"
    
    log_info "Processing trip: $trip_id"
    
    # Parse trip ID
    local trip_date=$(echo "$trip_id" | cut -d'T' -f 1)
    local trip_year=$(echo "$trip_date" | cut -d'-' -f 1)
    local trip_month=$(echo "$trip_date" | cut -d'-' -f 2)
    local trip_day=$(echo "$trip_date" | cut -d'-' -f 3)
    
    # Construct S3 path
    local s3_path="s3://$S3_BUCKET/$S3_PREFIX/$trip_year/$trip_month/$trip_day/$trip_id.tar"
    local local_tar_path="$OUTPUT_DIR/$trip_id.tar"
    
    log_verbose "S3 path: $s3_path"
    log_verbose "Local tar path: $local_tar_path"
    
    # Check if S3 object exists
    log_verbose "Checking if S3 object exists..."
    if ! aws s3 ls "$s3_path" &> /dev/null; then
        log_error "Trip not found in S3: $s3_path"
        return 1
    fi
    
    # Download from S3
    log_info "Downloading $trip_id.tar..."
    if ! aws s3 cp "$s3_path" "$local_tar_path"; then
        log_error "Failed to download from S3: $s3_path"
        return 1
    fi
    
    # Extract tar file
    log_info "Extracting $trip_id.tar..."
    if ! tar -xf "$local_tar_path" -C "$OUTPUT_DIR"; then
        log_error "Failed to extract tar file: $local_tar_path"
        return 1
    fi
    
    # Remove tar file
    log_verbose "Removing tar file..."
    rm -f "$local_tar_path"
    
    # Remove heavy directories if requested
    if [[ "$REMOVE_HEAVY_DIRS" == true ]]; then
        remove_heavy_directories "$OUTPUT_DIR/$trip_id"
    fi
    
    log_success "Successfully processed trip: $trip_id"
    return 0
}

# Parse command line arguments
TRIP_IDS=()
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output-dir)
            if [[ -n "${2:-}" ]]; then
                OUTPUT_DIR="$2"
                shift 2
            else
                log_error "Output directory not specified"
                exit 2
            fi
            ;;
        -r|--remove-heavy)
            REMOVE_HEAVY_DIRS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -b|--bucket)
            if [[ -n "${2:-}" ]]; then
                S3_BUCKET="$2"
                shift 2
            else
                log_error "S3 bucket not specified"
                exit 2
            fi
            ;;
        -p|--prefix)
            if [[ -n "${2:-}" ]]; then
                S3_PREFIX="$2"
                shift 2
            else
                log_error "S3 prefix not specified"
                exit 2
            fi
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_help
            exit 2
            ;;
        *)
            TRIP_IDS+=("$1")
            shift
            ;;
    esac
done

# Validate arguments
if [[ ${#TRIP_IDS[@]} -eq 0 ]]; then
    log_error "No trip IDs provided"
    show_help
    exit 2
fi

# Create output directory if it doesn't exist
if [[ ! -d "$OUTPUT_DIR" ]]; then
    log_info "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Check dependencies
if ! check_dependencies; then
    exit 3
fi

# Process each trip
log_info "Starting download of ${#TRIP_IDS[@]} trip(s)"
log_info "Output directory: $OUTPUT_DIR"
log_info "Remove heavy directories: $REMOVE_HEAVY_DIRS"

success_count=0
failure_count=0

for trip_id in "${TRIP_IDS[@]}"; do
    if ! validate_trip_id "$trip_id"; then
        ((failure_count++))
        continue
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would download: $trip_id"
        continue
    fi
    
    if download_trip "$trip_id"; then
        ((success_count++))
    else
        ((failure_count++))
    fi
done

# Summary
log_info "Download summary:"
log_info "  Successful: $success_count"
log_info "  Failed: $failure_count"

if [[ $failure_count -gt 0 ]]; then
    exit 1
else
    log_success "All trips downloaded successfully!"
    exit 0
fi
