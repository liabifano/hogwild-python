# Hogwild Python Implementation

[HOGWILD!](https://arxiv.org/abs/1106.5730)

## Configurations and setup
To build the python environment and activate it run: 
```bash
bash bootstrap-python-env.sh
source activate hogwild-python
```

All definitions about the coordinator address, nodes addresses and parameters related with SGD execution are in the file `settings.py`. We assume that at least two workers will be started.

To generate the proto classes (definition of message between nodes and coordinator), run the following command inside the hogwild folder:
```bash
source activate hogwild-python
cd src/hogwild & python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. hogwild.proto
```
If you made any change in the file `.proto`, you must generate the classes again

## Run tests
```bash
source activate hogwild-python 
py.test --color=yes -v
```

## Run
The flag `-n` represents the number of nodes, `-r` the running mode (synchronous or asynchronous) and `-w` where it is gonna run (local or cluster)
##### To run local:
```bash
bash run.sh -w synchronous -w local
```
and it will spin 4 workers in our local machine.

##### To run in the cluster:
```bash
bash run.sh -n 3 -r synchronous -w cluster
```
and it will spin 3 workers in Kubernetes cluster. Don't forget the change the variables `KUBER_LOGIN` and docker hub user / password inside the script before to run. 
