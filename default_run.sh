#!/bin/bash
mkdir -p "res"
DIR="defaultres"
mkdir "res/$DIR"
mkdir "res/$DIR/graph"
mkdir "res/$DIR/graph_data"

start_time=$(date +%s)

python3 src/main.py  1> ./res/"$DIR"/logs.txt
python3 src/animation.py "res/$DIR/graph"

end_time=$(date +%s)
elapsed_time=$((end_time - start_time))
echo "Simulation takes $elapsed_time seconds"

CURRENT_DIR=$(basename "$PWD")
cd ./res
zip -r "${CURRENT_DIR}_res.zip" *
mv "${CURRENT_DIR}_res.zip" ..
