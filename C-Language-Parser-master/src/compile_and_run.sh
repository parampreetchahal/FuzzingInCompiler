#!/bin/bash

INPUT_FILE=$1

# Step 1: Parse the file
./parser < "$INPUT_FILE"
if [ $? -eq 0 ]; then
    echo "Parsing successful, compiling..."
    
    # Step 2: Compile the file
    gcc "$INPUT_FILE" -o output_exe

    # Step 3: Run the executable if compilation succeeded
    if [ $? -eq 0 ]; then
        echo "Running the program:"
        ./output_exe
    else
        echo "GCC Compilation Failed."
    fi
else
    echo "Parsing failed, not compiling."
fi

