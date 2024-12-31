#!/bin/bash
rm -rf datamain
rm -rf datagroup
mkdir datamain
mkdir datagroup

cp ./dataprocess_group.ipynb ./datagroup/dataprocess.ipynb
cp ./utils_group.py ./datagroup/utils.py

cp ./dataprocess_main.ipynb ./datamain/dataprocess.ipynb
cp ./utils_main.py ./datamain/utils.py

#!/bin/bash

# Seed values
seed_array=(10 20 30 40 50)

# Loop through seed values
for seed in "${seed_array[@]}"; do
    filename="seed${seed}"
    echo "Processing $filename"
    
    # Navigate to the folder and clean up
    cd "${filename}" || { echo "Directory $filename not found!"; exit 1; }
    rm -rf main
    rm -rf group
    mkdir main
    mkdir group

    # Input array for values
    input_array=(10000 20000 30000 40000 50000 60000 70000) # Modify this array as needed

    # Process each value in input_array
    for value in "${input_array[@]}"; do
        destination_path="./main${value}/main${value}_res.zip"
        if [ -f "$destination_path" ]; then
            #echo "$destination_path"
            unzip "$destination_path"
            mv defaultres "./main/${value}"
        else
            echo "File $destination_path not found!"
        fi

        destination_path="./group${value}/group${value}_res.zip"
        if [ -f "$destination_path" ]; then
            #echo "$destination_path"
            unzip "$destination_path"
            mv defaultres "./group/${value}"
        else
            echo "File $destination_path not found!"
        fi
    done

    # Return to the parent directory
    cd ..
done


