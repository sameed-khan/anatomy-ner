#!/bin/bash

# Maximum number of background jobs
max_jobs=48

# Create a temporary file to store file paths and their word counts
temp_file=$(mktemp)

# Get the total number of files
file_paths=( $(find /home/sameed/charit/anatomy-ner/mimic_cxr_reports -type f -name *.txt) )
total_files=${#file_paths[@]}

# Initialize a counter for the processed files
processed_files=0

# Function to process a file
process_file() {
    file=$1
    # Check if the file contains the string "FINDINGS:"
    if grep -q "FINDINGS:" $file; then
        # Get the word count of the substring between "FINDINGS:" and "IMPRESSION"
        # word_count=$(awk '/FINDINGS:/, /IMPRESSION/' $file | grep -v "IMPRESSION" | wc -w)
        word_count=$(awk '/FINDINGS:/, /IMPRESSION/' $file | grep -v "IMPRESSION" | grep -o '\.' | wc -l)
        # Write the file path and the word count to the temporary file
        echo "$file $word_count" >> $temp_file
    fi
    # Increment the counter for the processed files
    ((processed_files++))
    # Calculate the progress
    progress=$((processed_files * 100 / total_files))
    # Display the progress bar
    printf "\r[%-50s] %d%%" $(printf '%.0s#' $(seq 1 $((progress / 2)))) $progress
}

# Iterate over all the files
for file in "${file_paths[@]}"
do
    # Process the file in the background
    process_file $file &

    # If the number of jobs is greater than the maximum
    while (( $(jobs -p | wc -l) >= max_jobs )); do
        # Wait for any job to finish
        sleep 1
    done
done

# Wait for all background processes to finish
wait

# Sort the file paths by word count and print the top 50
sort -rn -k2 $temp_file > /home/sameed/charit/anatomy-ner/data/report_lengths.txt

# Remove the temporary file
rm $temp_file