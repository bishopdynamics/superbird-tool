#!/usr/bin/env bash

# build a standalone binary for superbird_tool

if [ "$(uname -s)" == "Darwin" ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3"
    OUTPUT_FILE="superbird_tool.bin"
elif [ "$(uname -s)" == "Linux" ]; then
    PYTHON_CMD="sudo python3"
    OUTPUT_FILE="superbird_tool.bin"
else
    # assume Windows
    PYTHON_CMD="python"
    OUTPUT_FILE="superbird_tool.exe"
fi

set -e  # bail on any errors

$PYTHON_CMD -m nuitka --onefile superbird_tool.py

# cleanup temp build files
if [ "$(uname -s)" == "Linux" ]; then
    sudo rm -r superbird_tool.build
    sudo rm -r superbird_tool.onefile-build
    sudo rm -r superbird_tool.dist
else
    rm -r superbird_tool.build
    rm -r superbird_tool.onefile-build
    rm -r superbird_tool.dist
fi

echo "Completed build of $OUTPUT_FILE"
