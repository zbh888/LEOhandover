# How to run

Well, you can run each experiment individually....
Or you can use this repo to batch run experiments, get the result, generate analysis

1. specify the seed and how many UEs you want to simulate in `run_experiment.sh`, default is 10.
  
2. Run `./run_experiment.sh`. (1. Need Linux environment becuase the use of `sed` 2. I suggest you do this in a server with `nohup`) 

3. So, after you waited for a few hours, you will see a folder namely `seed10`, which contains GHO and HO results.

4. Suppose you have run with different seed and obtain folders `seed10`, `seed20`, `seed30`, `seed40`, `seed50`. 

5. You could use `copy_res_local.sh`  to process results. Here, I provided the result folder that can be downloaded https://drive.google.com/file/d/12G8Q1eSfHVpzL0Rb21YSic8ATTGOBTJd/view?usp=drive_link.

7. If you want to aggregate the result from different seeds, you can use these pickle files. Format them like in the example folder `datagroup` and `datamain`.

8. Now you can use `data_aggregate_seeds` notebook to generate the results.
