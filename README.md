# LEO handover

The handover process is implemented in discrete-event tool "simpy"

# How to run the code

1. go to ./src/config.py to apply your experiment setting.

2. `./default_run.sh`

3. `./clean.sh` if you want to remove everything.

(You can batch run everything and generate results, check `result` branch)

# branches

`main`: Xn-based baseline handover, location based trigger

`group`: group Xn-based handover, location based trigger

`result`: batch running experiments and generate analysis

# animations (HO vs GHO)
(HO draw every 200 ms, GHO draw every 300 ms, why? I forgot to change it....)


<p align="center">
  <img width="200" src=./gifs/main10000.gif>
  <img width="200" src=./gifs/group10000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main20000.gif>
  <img width="200" src=./gifs/group20000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main30000.gif>
  <img width="200" src=./gifs/group30000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main40000.gif>
  <img width="200" src=./gifs/group40000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main50000.gif>
  <img width="200" src=./gifs/group50000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main60000.gif>
  <img width="200" src=./gifs/group60000.gif>
</p>
<p align="center">
  <img width="200" src=./gifs/main70000.gif>
  <img width="200" src=./gifs/group70000.gif>
</p>
