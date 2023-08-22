#!/bin/bash

DIR="res"
mkdir "res/$DIR"
mkdir "res/$DIR/graph"
python3 src/main.py "$DIR" 1> ./res/"$DIR"/logs.txt
