# Hogwild Python Implementation

[HOGWILD!](https://arxiv.org/abs/1106.5730)

The implementation consists in one coordinator and `n` working nodes. 

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

<img src="resources/temp_schema_comunication.jpeg"
     alt="Markdown Monster icon"
     style="float: left; margin-right: 10px;" />


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
ps: make sure that the file `setting.py` has the right ports and addresses

Then run the coordinator:
```bash
source activate hogwild-python 
python src/hogwild/coordinator.py
```

## TODOs:
- shell script to spin all nodes and coordinator
- write unit tests 
- write documentation
- control / recovery of failures
- asynchronous version 