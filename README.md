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
