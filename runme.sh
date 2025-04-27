#!/usr/bin/env bash

# Exit on errors
set -e

# Default settings
CLEANUP_FILES=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --clean-files)
      CLEANUP_FILES=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --keep-files    Don't delete old files in workarea"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Define the virtual environment directory
VENV_DIR="$SCRIPT_DIR/venv"
# Define the requirements file
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
# Define the workarea directory
WORKAREA_DIR="workarea"

# Check if python3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is not installed. Please install it first."
    exit 1
fi
if ! command -v pip &> /dev/null; then
    echo "pip is not installed. Please install it first."
    exit 1
fi

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

# Create and prepare workarea directory
echo "Setting up workarea directory..."
mkdir -p "$WORKAREA_DIR"

# Clean up old files if requested
if [ "$CLEANUP_FILES" = true ]; then
    echo "Cleaning up files older than 7 days in workarea..."
    find "$WORKAREA_DIR" -type f -mtime +7 -delete 2>/dev/null || true
else
    echo "Keeping existing files in workarea directory."
fi

# Activate virtual environment and run the program
echo "Activating virtual environment and starting program..."
source "$VENV_DIR/bin/activate"

# Export the workarea directory as an environment variable
export SAGE_WORKAREA="$WORKAREA_DIR"

# Save current directory
ORIGINAL_DIR=$(pwd)

# Change to workarea directory
echo "Changing to workarea directory: $WORKAREA_DIR"
mkdir -p "$WORKAREA_DIR"  # Ensure it exists
cd "$WORKAREA_DIR"

# Run the main program from the workarea directory
echo "Running main program from workarea directory..."
python "$SCRIPT_DIR/main.py"

# Return to original directory
echo "Returning to original directory..."
cd "$ORIGINAL_DIR"

# Deactivate virtual environment when done
echo "Program exited. Deactivating virtual environment..."
deactivate
