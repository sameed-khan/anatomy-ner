#!/bin/bash

# Change directory to current directory that the script lives in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR/../.."

# Maximum number of background jobs
max_jobs=30

# Create a temporary file to store file paths and their word counts
temp_file=$(mktemp)

# Get the total number of files
file_paths=( $(find mimic_cxr_reports -type f -name \*.txt) )
total_files=${#file_paths[@]}

# Initialize a counter for the processed files
processed_files=0

# Function to update the progress bar
update_progress_bar() {
    progress=$((processed_files * 100 / total_files))
    printf "\r[%-50s] %d%%" $(printf '%.0s#' $(seq 1 $((progress / 2)))) "$progress"
}

# Function to process a file
process_file() {
    file=$1

    # Check if the file contains the string "FINDINGS:"
    if grep -q "FINDINGS:" "$file"; then
        # Get the word count of the substring between "FINDINGS:" and "IMPRESSION"
        # word_count=$(awk '/FINDINGS:/, /IMPRESSION/' "$file" | grep -v "IMPRESSION" | wc -w)
        word_count=$(awk '/FINDINGS:/, /IMPRESSION/' "$file" | grep -v "IMPRESSION" | grep -o '\.' | wc -l)

        # Write the file path and the word count to the temporary file
        echo "$file $word_count" >> "$temp_file"
    fi

    # Increment the counter for the processed files
    ((processed_files++))
}

# Iterate over all the files
for file in "${file_paths[@]}"; do
    # Process the file in the background
    process_file "$file" &

    # If the number of jobs is greater than the maximum
    while (( $(jobs -p | wc -l) >= max_jobs )); do
        # Update the progress bar
        update_progress_bar

        # Wait for any job to finish
        sleep 1
    done
done

# Wait for all background processes to finish
wait

# Update the progress bar one last time to show 100%
update_progress_bar
echo ""

# Sort the file paths by word count and print the top 50
sort -rn -k2 "$temp_file" > data/report_lengths.txt

# Remove the temporary file
rm "$temp_file"
