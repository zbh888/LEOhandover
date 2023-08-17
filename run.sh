#!/bin/bash

if [ -e "res.txt" ]; then
    echo "Result exists. Clean up."
    exit 1
fi
python3 src/main.py 1> res.txt
