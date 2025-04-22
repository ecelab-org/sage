#!/usr/bin/env bash

# Exit on errors
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# Check if requirements.txt exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Creating requirements.txt file..."
    echo "python-dotenv>=1.1" > "$REQUIREMENTS_FILE"
fi

# Function to create virtual environment
create_venv() {
    echo "Creating virtual environment..."
    python3.11 -m venv "$VENV_DIR"
    touch "$VENV_DIR/.last_update"
}

# Function to update virtual environment
update_venv() {
    echo "Updating virtual environment..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
    touch "$VENV_DIR/.last_update"
}

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found."
    create_venv
    update_venv
else
    echo "Virtual environment found."

    # Check if requirements.txt has been modified since last update
    VENV_LAST_UPDATE=$(stat -c %Y "$VENV_DIR/.last_update" 2>/dev/null || echo 0)
    REQUIREMENTS_LAST_MODIFIED=$(stat -c %Y "$REQUIREMENTS_FILE" 2>/dev/null || echo 0)

    if [ "$REQUIREMENTS_LAST_MODIFIED" -gt "$VENV_LAST_UPDATE" ]; then
        echo "Requirements file has been modified since last update."
        update_venv
    else
        echo "Requirements file hasn't changed. Using existing virtual environment."
    fi
fi

# Activate virtual environment and run the program
echo "Activating virtual environment and starting program..."
source "$VENV_DIR/bin/activate"

# Run the main program
python "$SCRIPT_DIR/main.py"

# Deactivate virtual environment when done
echo "Program exited. Deactivating virtual environment..."
deactivate
