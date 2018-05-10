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

## Synchronous execution
Open `n+1` terminals where `n` is the number of nodes. First run each node with the selected port number as an argument. Eg:
```bash
source activate hogwild-python 
python src/hogwild/nodes.py 50052
```
> **NOTE** make sure that the file `settings.py` has the right ports and addresses

Then run the coordinator. Its port is specified in `settings.py`:
```bash
source activate hogwild-python 
python src/hogwild/coordinator.py
```

## Considerations about Synchronous execution
 
`n` = # number of nodes

`eps` = # number of epochs

- **What is the data that is constant?**
Entire dataset.

- **How much data is sent?**
For each epoch, each node sends a dictionary with on average 75 values (non-null entries) to all others nodes.
So the total amount is about 75\*n\*(n+1)\*eps.

- **How many messages are sent through the network?**
For each epoch n\*(n+1), which is quadratic in relation the number of nodes.
As we don't expect a large number of nodes and all of them are the same geographical regions (distance latency is small), then this is not a huge problem.

- **Taking subsets of the data to compute for each epoch**
As in the chapter 2 of the HOGWILD! paper, for every epoch, every node calculates the gradient of a small subset of the dataset. The benefits of this are that we can keep communication between the nodes to a minimum. Even though the messages carrying the weight updates are bigger, the total latency of sending all the messages will be smaller.

## Considerations about Asynchronous implementation
We built the synchronous version keeping in mind that the shared codebase with the asynchronous version should be as large as possible. The coordinator remains the same, specifying if the nodes should work in synchronous or asynchronous mode. It will as before simply listen to and save all the weight changes that it receives.

On the other hand, the nodes will move on with their computation without checking the state of all the other nodes or waiting for them to finish some computation. The nodes will now get the last values that they received and start another computation when they are ready.

Another idea to reduce the number of comunication in the network is have a cached database in the server node which stores all messages in a queue and the nodes send the weights updates and consultes the same database to get the last weigths updates stored. However the database troughtput might be a bottleneck.

## TODOs:
- [ ] Dockerize things
- [ ] Deploy in Kubernetes
- [ ] Fix sync: change Coordinator rule to syncronize everyone
- [ ] Put epoch number in each message 
- [ ] Stop Criterion based in loss
- [ ] Multithreading in the nodes
- [ ] Write unit tests
- [ ] Asynchronous HOGWILD! like version
