# Hogwild Python Implementation

[HOGWILD!](https://arxiv.org/abs/1106.5730)

The implementation consists in one coordinator and `n` working nodes. 
As the dataset is constant, fits in the node memory and it will be required to be accessed by all the nodes multiple times (for each epoch), it will be sent to every node in the beginning of the job.
We define an epoch as one iteration of SGD over a random subsample of the dataset.

For now, the responsibilities of coordinator node are:
1. Split dataset in train / test
2. Send to the nodes the entire train dataset and all nodes addresses 
3. Listen intermediate result of working nodes
4. After the working nodes' job is completed, will aggregate the weight updates and calculate the model's performance in the test dataset.

The responsibilities of the working nodes are:
1. Receive the dataset and send message to all others nodes and to coordinator that its is ready to start the computations.
2. Wait until all others nodes are ready to start the computations
3. Performance one `epoch` of computation
4. Send to all others nodes the result and that it is ready to start another `epoch`
5. Wait until all others nodes are ready to start another `epoch`
6. Send a message to the coordinator stating that all epochs are done

In summary:

![stack](/resources/temp_schema_comunication.JPG)

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
bash run.sh -n 3 -w synchronous -w cluster
```
and it will spin 3 workers in Kubernetes cluster. Don't forget the change the variables `KUBER_LOGIN` and docker hub user / password inside the script before to run. 
