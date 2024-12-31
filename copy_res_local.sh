#!/bin/bash
seed=50
filename="seed${seed}"
cd "${filename}"

mkdir main
mkdir group

cp ../dataprocess_group.ipynb ./group/dataprocess.ipynb
cp ../utils_group.py ./group/utils.py

cp ../dataprocess_main.ipynb ./main/dataprocess.ipynb
cp ../utils_main.py ./main/utils.py


input_array=(10000 20000 30000 40000 50000 60000 70000) # Modify this array with your desired values

for value in "${input_array[@]}"; do
	destination_path="./main${value}/main${value}_res.zip"
	unzip $destination_path
	mv defaultres "./main/${value}"

	destination_path="./group${value}/group${value}_res.zip"
	unzip $destination_path
	mv defaultres "./group/${value}"
done

cd ..

