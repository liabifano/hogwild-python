# Hogwild Python Implementation

[HOGWILD!](https://arxiv.org/abs/1106.5730)

The implementation consists in one coordinator and `n` working nodes. 
As the dataset is constant, fits in the node memory and it will be required to be accessed by all the nodes multiple times (for each epoch), it will be sent to every node in the beginning of the job.
Each epoch is one interaction of a SGD over a random subsample of the dataset.

For now, the responsibilities of coordinator node are:
1. Split dataset in train / test
2. Send to the nodes the entire train dataset and all nodes addresses 
3. Listen intermediate result of working nodes
4. After the working nodes' job is completed, will compute aggregate the computation and calculate the model's performance in the test dataset.

The responsibilities of the working nodes are:
1. Receive the dataset and send message to all others nodes and to coordinator that its is ready to start the computations.
2. Wait until all others nodes are ready to start the computations
3. Performance `epoch` computation
4. Send to all others nodes the result and that its is ready to start another `epoch`
5. Wait until all others nodes are ready to start another `epoch`
6. Send the final result to coordinator node

In summary:

![stack](/resources/temp_schema_comunication.JPG)

## Configurations and setup
To build the python environment and activate it run: 
```bash
bash bootstrap-python-env.sh
source activate hogwild-python
```

To run unit tests run:
```bash
source activate hogwild-python
py.test
```

All definitions about the coordinator address, nodes addresses and parameters related with SGD execution are in the file `settings.py`

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

## Synchronous execution
Open `n+1` terminals where `n` is the number of nodes. First run each node with the selected port number as an argument. Eg:
```bash
source activate hogwild-python 
python src/hogwild/nodes.py 50052
```
> **NOTE** make sure that the file `setting.py` has the right ports and addresses

Then run the coordinator:
```bash
source activate hogwild-python 
python src/hogwild/coordinator.py
```

## Considerations about Synchronous execution
 
`n` = # number of nodes

`eps` = # number of epochs

As the dataset is constant, fits in the memory of each node and it will be required to be accessed by all the nodes multiple times (for epoch)

- **What is the data that is constant?**
Entire dataset.

- **How much data is send?**
For each epoch, each node sends a dictionary with average 75 values (non-null entries) to all others nodes.
So the total amount is about 75\*n\*(n+1)*ep.

- **How many messages are sent trough the network?**
For each epoch n\*(n+1), which is quadratic in relation the number of nodes.
As we don't expect a large number of nodes and all of them are the same geographical regions (distance latency is small), then this is not a huge problem.

## TODOs:
- shell script to spin all nodes and coordinator
- write unit tests 
- write documentation
- control / recovery of failures
- asynchronous version 