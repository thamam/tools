#!/bin/bash

# A script to interactively scan single or double-sided documents to PDF.

echo "========================================"
echo " Interactive Document Scanner (v2)"
echo "========================================"
echo

# --- Configuration ---
# The scanner device name is hardcoded because auto-detection is complex in a simple script.
# This is the device name we discovered for your scanner.
SCANNER_DEVICE="brother4:bus1;dev6"
TEMP_DIR="/home/thh3/Downloads/scan_temp"

echo "Using scanner: $SCANNER_DEVICE"
echo

# --- Get user input ---
read -p "Enter the name for the final PDF file (e.g., my_document.pdf): " OUTPUT_FILENAME

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
    echo "Combining pages into PDF..."
    # This will take all .pnm files in the directory
    img2pdf "$TEMP_DIR"/*.pnm -o "/home/thh3/Downloads/$OUTPUT_FILENAME"

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
    read -p "IMPORTANT: Please enter the number of pages that were just scanned: " NUM_FRONT
    echo "Noted: $NUM_FRONT front pages."
    echo

    # --- Scan back pages (with loop for correction) ---
    while true; do
        echo "----------------------------------------"
        echo "      DOUBLE-SIDED SCAN: BACK PAGES"
        echo "----------------------------------------"
        echo "Based on your feedback, we need to adjust the paper orientation for the back-side scan."
        echo "1. Take the stack of $NUM_FRONT pages from the output tray."
        echo "2. Rotate the entire stack 180 degrees (like a spinning wheel)."
        echo "3. Place the rotated stack back into the feeder."
        echo
        read -p "Press Enter when you are ready to scan the BACK pages..."

        echo "Scanning back pages..."
scanimage -d "$SCANNER_DEVICE" --mode Gray --resolution 300 --batch="$BACK_DIR/back_%03d.pnm" --source "Automatic Document Feeder(left aligned)" -p
        
        echo
        read -p "IMPORTANT: Please enter the number of BACK pages that were just scanned: " NUM_BACK
        echo "Noted: $NUM_BACK back pages."
        echo

        if [ "$NUM_FRONT" -eq "$NUM_BACK" ]; then
            break # Numbers match, exit loop
        else
            echo "Error: The number of front pages ($NUM_FRONT) does not match the number of back pages ($NUM_BACK)."
            read -p "Would you like to try scanning the back pages again? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Clearing back pages directory and trying again..."
                rm "$BACK_DIR"/*
            else
                echo "Aborting scan."
                exit 1
            fi
        fi
    done

    # --- Rotate the back pages ---
    echo "Rotating back pages 180 degrees..."
 mogrify -rotate 180 "$BACK_DIR"/*.pnm

    # --- Combine interleaved pages ---
    echo "Combining and interleaving pages into PDF..."
    FILE_LIST=""
    i=1
    while [ $i -le $NUM_FRONT ]; do
        # Format i with leading zeros like 001, 002 etc.
        printf -v I_FORMATTED "%03d" $i
        
        # Calculate the index for the back page (in reverse)
        back_i=$((NUM_FRONT - i + 1))
        printf -v BACK_I_FORMATTED "%03d" $back_i

        FILE_LIST="$FILE_LIST \"$FRONT_DIR/front_$I_FORMATTED.pnm\" \"$BACK_DIR/back_$BACK_I_FORMATTED.pnm\""
        i=$((i + 1))
    done

    # Using eval to handle the file list with spaces correctly
    eval "img2pdf $FILE_LIST -o \"/home/thh3/Downloads/$OUTPUT_FILENAME\""

fi

# --- Cleanup ---
echo
read -p "Do you want to delete the temporary scan files in $TEMP_DIR? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting temporary files..."
    rm -r "$TEMP_DIR"
fi

echo
echo "========================================"
echo "          Scan Complete!"
echo "========================================"
echo "Your file is saved as: /home/thh3/Downloads/$OUTPUT_FILENAME"
echo