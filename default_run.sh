#!/bin/bash
DIR="defaultres"
mkdir "res/$DIR"
mkdir "res/$DIR/graph"
python3 src/main.py  1> ./res/"$DIR"/logs.txt
