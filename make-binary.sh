#!/usr/bin/env bash

# build a standalone binary for superbird_tool

if [ "$(uname -s)" == "Darwin" ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3"
elif [ "$(uname -s)" == "Linux" ]; then
    PYTHON_CMD="sudo python3"
else
    # assume Windows
    PYTHON_CMD="python"
fi

set -e  # bail on any errors

$PYTHON_CMD -m nuitka --follow-imports superbird_tool.py

# cleanup temp build files
if [ "$(uname -s)" == "Linux" ]; then
    sudo rm -r superbird_tool.build
else
    rm -r superbird_tool.build
fi

echo "Completed build of superbird_tool binary"
