#!/bin/bash
mkdir -p "res"
DIR="defaultres"
mkdir "res/$DIR"
mkdir "res/$DIR/graph"
mkdir "res/$DIR/graph_data"
python3 src/main.py  1> ./res/"$DIR"/logs.txt
python3 src/animation.py "res/$DIR/graph"
