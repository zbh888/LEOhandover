#!/bin/bash
seed=50
filename="seed${seed}"
mkdir "${filename}"
cd "${filename}"

mkdir main
mkdir group

cp ../dataprocess_group.ipynb ./group/dataprocess.ipynb
cp ../utils_group.py ./group/utils.py

cp ../dataprocess_main.ipynb ./main/dataprocess.ipynb
cp ../utils_main.py ./main/utils.py


input_array=(10000 20000 30000 40000 50000 60000 70000) # Modify this array with your desired values

for value in "${input_array[@]}"; do
	source_path="b327zhan@linux.cs.uwaterloo.ca:./${filename}/main${value}/main${value}_res.zip"
	destination_path="./${filename}_main${value}_res.zip"
	scp $source_path $destination_path
	unzip $destination_path
	mv defaultres "./main/${value}"

	source_path="b327zhan@linux.cs.uwaterloo.ca:./${filename}/group${value}/group${value}_res.zip"
	destination_path="./${filename}_group${value}_res.zip"
	scp $source_path $destination_path
	unzip $destination_path
	mv defaultres "./group/${value}"
done

cd ..
