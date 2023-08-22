#!/bin/bash
counter=0
mkdir -p "res"
for cpu in 8 16 32 64 128; do
    for delay in 1 5 10 15 20 25 30; do
        counter=$((counter + 1))
        mkdir "res/$counter"
        mkdir "res/$counter/graph"
        python3 src/main.py "$counter" "$cpu" "$delay" 1> ./res/"$counter"/logs.txt 
    done
done
