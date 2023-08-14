#!/bin/bash

if [ -e "res.txt" ]; then
    echo "Result exists. Terminating the process."
    exit 1
fi
python3 src/main.py 1> res.txt
