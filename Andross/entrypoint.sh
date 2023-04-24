#!/bin/bash

if [ "$1" == "start" ]; then
    python app.py
elif [ "$1" == "shell" ]; then
    /bin/bash
else
    echo "Unknown command: $1"
    exit 1
fi
