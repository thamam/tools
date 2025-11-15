#!/bin/bash

# A script to interactively scan single or double-sided documents to PDF.

echo "========================================"
echo " Interactive Document Scanner (v3)"
echo "========================================"
echo

# --- Configuration ---
# The scanner device name is hardcoded because auto-detection is complex in a simple script.
# This is the device name we discovered for your scanner.
SCANNER_DEVICE="brother4:bus1;dev6"
TEMP_DIR="/home/thh3/Downloads/scan_temp"

echo "Using scanner: $SCANNER_DEVICE"
echo

# --- Helper Functions ---

# Function to auto-orient images using tesseract
auto_orient_images() {
    local dir="$1"
    echo "Auto-detecting and correcting orientation..."
    for img in "$dir"/*.pnm; do
        if [ -f "$img" ]; then
            # Use tesseract to detect orientation and rotate if needed
            orientation=$(tesseract "$img" - --psm 0 2>&1 | grep "Orientation in degrees" | awk '{print $4}')
            if [ ! -z "$orientation" ] && [ "$orientation" != "0" ]; then
                echo "  Rotating $(basename "$img") by $orientation degrees..."
                mogrify -rotate "$orientation" "$img"
            fi
        fi
    done
}

# Function to perform OCR on images and generate text
perform_ocr() {
    local dir="$1"
    local output_file="$2"
    echo "Performing OCR..."
    > "$output_file"  # Clear the file
    for img in "$dir"/*.pnm; do
        if [ -f "$img" ]; then
            echo "  Processing $(basename "$img")..."
            tesseract "$img" stdout -l eng >> "$output_file" 2>/dev/null
            echo -e "\n--- Page Break ---\n" >> "$output_file"
        fi
    done
}

# Function to generate markdown from OCR text
generate_markdown() {
    local text_file="$1"
    local md_file="$2"
    echo "Generating Markdown..."
    {
        echo "# Scanned Document"
        echo ""
        echo "Generated on: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "---"
        echo ""
        cat "$text_file"
    } > "$md_file"
}

# --- Get user input ---
read -p "Enter the name for the final output file (e.g., my_document): " OUTPUT_FILENAME

if [ -z "$OUTPUT_FILENAME" ]; then
    echo "Error: Output filename cannot be empty."
    exit 1
fi

echo
echo "Is this a single-sided or double-sided scan?"
select SCAN_MODE in "Single-sided" "Double-sided"; do
    case $SCAN_MODE in
        "Single-sided" ) break;;
        "Double-sided" ) break;;
    esac
done

echo
echo "Select output format:"
select OUTPUT_FORMAT in "PDF" "PDF with OCR" "Text (OCR)" "Markdown (OCR)"; do
    case $OUTPUT_FORMAT in
        "PDF" ) break;;
        "PDF with OCR" ) break;;
        "Text (OCR)" ) break;;
        "Markdown (OCR)" ) break;;
    esac
done

# --- Create temp directory ---
if [ -d "$TEMP_DIR" ]; then
    read -p "A temporary directory from a previous scan exists. Delete it and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -r "$TEMP_DIR"
    else
        echo "Aborting. Please remove the directory $TEMP_DIR and try again."
        exit 1
    fi
fi
mkdir -p "$TEMP_DIR"
echo "Using temporary directory: $TEMP_DIR"
echo

# --- Main scanning logic ---
if [ "$SCAN_MODE" == "Single-sided" ]; then
    # --- SINGLE-SIDED SCAN ---
    echo "----------------------------------------"
    echo "        SINGLE-SIDED SCAN MODE"
    echo "----------------------------------------"
    echo "1. Place your stack of documents in the document feeder with the front sides facing UP."
    echo "2. The top edge of the pages should go into the scanner first."
    echo
    read -p "Press Enter when you are ready to scan..."

    echo "Scanning..."
    scanimage -d "$SCANNER_DEVICE" --mode Gray --resolution 300 --batch="$TEMP_DIR/page_%03d.pnm" --source "Automatic Document Feeder(left aligned)" -p

    echo
    # Auto-orient all scanned pages
    auto_orient_images "$TEMP_DIR"

    # Generate output based on selected format
    case "$OUTPUT_FORMAT" in
        "PDF" )
            echo "Combining pages into PDF..."
            img2pdf "$TEMP_DIR"/*.pnm -o "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf"
            ;;
        "PDF with OCR" )
            echo "Creating searchable PDF with OCR..."
            # First create a temporary text file for OCR
            OCR_TEMP="$TEMP_DIR/ocr_temp.txt"
            perform_ocr "$TEMP_DIR" "$OCR_TEMP"
            # Create PDF with img2pdf and then add OCR layer
            img2pdf "$TEMP_DIR"/*.pnm -o "$TEMP_DIR/temp.pdf"
            # Use ocrmypdf for searchable PDF
            if command -v ocrmypdf &> /dev/null; then
                ocrmypdf "$TEMP_DIR/temp.pdf" "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf" --force-ocr
            else
                echo "Warning: ocrmypdf not found. Creating regular PDF instead."
                mv "$TEMP_DIR/temp.pdf" "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf"
            fi
            ;;
        "Text (OCR)" )
            perform_ocr "$TEMP_DIR" "/home/thh3/Downloads/$OUTPUT_FILENAME.txt"
            ;;
        "Markdown (OCR)" )
            OCR_TEMP="$TEMP_DIR/ocr_temp.txt"
            perform_ocr "$TEMP_DIR" "$OCR_TEMP"
            generate_markdown "$OCR_TEMP" "/home/thh3/Downloads/$OUTPUT_FILENAME.md"
            ;;
    esac

else
    # --- DOUBLE-SIDED SCAN ---
    FRONT_DIR="$TEMP_DIR/front"
    BACK_DIR="$TEMP_DIR/back"
    mkdir -p "$FRONT_DIR" "$BACK_DIR"

    # --- Scan front pages ---
    echo "----------------------------------------"
    echo "     DOUBLE-SIDED SCAN: FRONT PAGES"
    echo "----------------------------------------"
    echo "1. Place your stack of documents in the document feeder with the front sides facing UP."
    echo "2. The top edge of the pages should go into the scanner first."
    echo
    read -p "Press Enter when you are ready to scan the FRONT pages..."

    echo "Scanning front pages..."
    scanimage -d "$SCANNER_DEVICE" --mode Gray --resolution 300 --batch="$FRONT_DIR/front_%03d.pnm" --source "Automatic Document Feeder(left aligned)" -p

    echo
    # Automatically count the number of front pages
    NUM_FRONT=$(ls -1 "$FRONT_DIR"/*.pnm 2>/dev/null | wc -l)
    echo "Scanned $NUM_FRONT front pages."
    echo

    # --- Scan back pages ---
    echo "----------------------------------------"
    echo "      DOUBLE-SIDED SCAN: BACK PAGES"
    echo "----------------------------------------"
    echo "1. Take the stack of pages from the output tray."
    echo "2. WITHOUT rotating, flip the stack over and place it back in the feeder."
    echo "   (The last page should now be on top, face-down)"
    echo
    read -p "Press Enter when you are ready to scan the BACK pages..."

    echo "Scanning back pages..."
    scanimage -d "$SCANNER_DEVICE" --mode Gray --resolution 300 --batch="$BACK_DIR/back_%03d.pnm" --source "Automatic Document Feeder(left aligned)" -p

    echo
    # Automatically count the number of back pages
    NUM_BACK=$(ls -1 "$BACK_DIR"/*.pnm 2>/dev/null | wc -l)
    echo "Scanned $NUM_BACK back pages."
    echo

    # Verify counts match
    if [ "$NUM_FRONT" -ne "$NUM_BACK" ]; then
        echo "Warning: Number of front pages ($NUM_FRONT) doesn't match back pages ($NUM_BACK)."
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborting scan."
            exit 1
        fi
        # Use the minimum of the two counts
        if [ "$NUM_FRONT" -lt "$NUM_BACK" ]; then
            NUM_PAGES=$NUM_FRONT
        else
            NUM_PAGES=$NUM_BACK
        fi
    else
        NUM_PAGES=$NUM_FRONT
    fi

    # --- Auto-orient pages ---
    auto_orient_images "$FRONT_DIR"
    auto_orient_images "$BACK_DIR"

    # --- Combine interleaved pages ---
    echo "Combining and interleaving pages..."

    # Create a temporary directory for interleaved pages
    COMBINED_DIR="$TEMP_DIR/combined"
    mkdir -p "$COMBINED_DIR"

    # Interleave front and back pages
    i=1
    page_num=1
    while [ $i -le $NUM_PAGES ]; do
        printf -v I_FORMATTED "%03d" $i
        printf -v PAGE_FORMATTED "%03d" $page_num

        # Copy front page
        if [ -f "$FRONT_DIR/front_$I_FORMATTED.pnm" ]; then
            cp "$FRONT_DIR/front_$I_FORMATTED.pnm" "$COMBINED_DIR/page_$PAGE_FORMATTED.pnm"
            page_num=$((page_num + 1))
        fi

        # Copy back page (in reverse order)
        back_i=$((NUM_PAGES - i + 1))
        printf -v BACK_I_FORMATTED "%03d" $back_i
        printf -v PAGE_FORMATTED "%03d" $page_num

        if [ -f "$BACK_DIR/back_$BACK_I_FORMATTED.pnm" ]; then
            cp "$BACK_DIR/back_$BACK_I_FORMATTED.pnm" "$COMBINED_DIR/page_$PAGE_FORMATTED.pnm"
            page_num=$((page_num + 1))
        fi

        i=$((i + 1))
    done

    # Generate output based on selected format
    case "$OUTPUT_FORMAT" in
        "PDF" )
            echo "Creating PDF..."
            img2pdf "$COMBINED_DIR"/*.pnm -o "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf"
            ;;
        "PDF with OCR" )
            echo "Creating searchable PDF with OCR..."
            img2pdf "$COMBINED_DIR"/*.pnm -o "$TEMP_DIR/temp.pdf"
            if command -v ocrmypdf &> /dev/null; then
                ocrmypdf "$TEMP_DIR/temp.pdf" "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf" --force-ocr
            else
                echo "Warning: ocrmypdf not found. Creating regular PDF instead."
                mv "$TEMP_DIR/temp.pdf" "/home/thh3/Downloads/$OUTPUT_FILENAME.pdf"
            fi
            ;;
        "Text (OCR)" )
            perform_ocr "$COMBINED_DIR" "/home/thh3/Downloads/$OUTPUT_FILENAME.txt"
            ;;
        "Markdown (OCR)" )
            OCR_TEMP="$TEMP_DIR/ocr_temp.txt"
            perform_ocr "$COMBINED_DIR" "$OCR_TEMP"
            generate_markdown "$OCR_TEMP" "/home/thh3/Downloads/$OUTPUT_FILENAME.md"
            ;;
    esac

fi

# --- Cleanup ---
echo
read -p "Do you want to delete the temporary scan files in $TEMP_DIR? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting temporary files..."
    rm -r "$TEMP_DIR"
fi

# Determine the output file extension based on format
case "$OUTPUT_FORMAT" in
    "PDF" | "PDF with OCR" )
        FINAL_FILE="/home/thh3/Downloads/$OUTPUT_FILENAME.pdf"
        ;;
    "Text (OCR)" )
        FINAL_FILE="/home/thh3/Downloads/$OUTPUT_FILENAME.txt"
        ;;
    "Markdown (OCR)" )
        FINAL_FILE="/home/thh3/Downloads/$OUTPUT_FILENAME.md"
        ;;
esac

echo
echo "========================================"
echo "          Scan Complete!"
echo "========================================"
echo "Your file is saved as: $FINAL_FILE"
echo "Output format: $OUTPUT_FORMAT"
echo