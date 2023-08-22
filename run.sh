#!/bin/bash
mkdir -p "res"
for cpu in 8 16 32 64 128 256 512; do
    for delay in 1 5 10 15 20 25 30; do
        DIR="${cpu}A${delay}"
        mkdir "res/$DIR"
        mkdir "res/$DIR/graph"
        python3 src/main.py "$DIR" "$cpu" "$delay" 1> ./res/"$DIR"/logs.txt 
    done
done
