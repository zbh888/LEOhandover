# How to run

Well, you can run each experiment individually....
Or you can use this repo to batch run experiments, get the result, generate analysis

1. specify the seed and how many UEs you want to simulate in `run_experiment.sh`, default is 10.
  
2. Run `./run_experiment.sh`. (1. Need Linux environment becuase the use of `sed` 2. I suggest you do this in a server so you can use `copy_res.sh` to get your result.) 

3. So, after you waited for a few hours, you will see a folder namely `seed10`, which contains GHO and HO results.

4. Suppose you have run with different seed and obtain folders `seed10`, `seed20`, `seed30`, `seed40`, `seed50`. If they are in a server, you could use `copy_res.sh` to get them.

5. If they are not in a server. You could use `copy_res_local.sh`  to get process result. Here, I provided the result folder that can be downloaded https://drive.google.com/file/d/12G8Q1eSfHVpzL0Rb21YSic8ATTGOBTJd/view?usp=drive_link.

6. If you want to aggregate the result from different seeds, you can go to folder `datagroup` and `datamain`. You need to run two notebook to generate pickle file.

7. Now you can use `data_aggregate_seeds` notebook to generate the results.
