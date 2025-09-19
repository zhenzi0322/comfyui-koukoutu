#!/bin/bash

echo "Installing Koukoutu ComfyUI Node dependencies..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Python is not available. Please ensure Python is installed and in PATH."
    exit 1
fi

# Use python3 if available, otherwise use python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Using Python command: $PYTHON_CMD"
echo "Installing required packages..."

$PYTHON_CMD -m pip install requests>=2.28.0
if [ $? -ne 0 ]; then
    echo "Failed to install requests"
    exit 1
fi

$PYTHON_CMD -m pip install Pillow>=9.0.0
if [ $? -ne 0 ]; then
    echo "Failed to install Pillow"
    exit 1
fi

$PYTHON_CMD -m pip install numpy>=1.21.0
if [ $? -ne 0 ]; then
    echo "Failed to install numpy"
    exit 1
fi

echo
echo "All dependencies installed successfully!"
echo "You can now restart ComfyUI to use the Koukoutu nodes."
echo
