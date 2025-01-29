#!/bin/bash

# Set the output directory for project tree files
OUTPUT_DIR="./project_trees"

# Ensure the output directory exists
mkdir -p $OUTPUT_DIR

# Number of iterations
ITERATIONS=10

for ((i=1; i<=ITERATIONS; i++)); do
    # Generate a timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # Define the output file with a timestamp
    OUTPUT_FILE="$OUTPUT_DIR/project_tree_$TIMESTAMP.txt"

    # Generate the project tree excluding specified directories
    find . -type d \( -name 'node_modules' -o -name '.git' -o -name '.venv' -o -path './data/mongodb' \) -prune -o -type f -print > $OUTPUT_FILE

    echo "[$i/$ITERATIONS] Project tree has been exported to $OUTPUT_FILE (excluding 'node_modules', '.git', '.venv', and '/data/mongodb' directories)."

    # Wait for 30 minutes before running the next iteration
    if [[ $i -lt $ITERATIONS ]]; then
        sleep 1800
    fi
done

echo "Script has completed $ITERATIONS iterations. Restart manually to run again."
