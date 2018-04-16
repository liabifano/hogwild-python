# Hogwild Python Implementation

[HOGWILD!](https://arxiv.org/abs/1106.5730)


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



## Synchronous execution
Open n+1 terminals where n is the number of nodes. First run each node with the selected port number as an argument. Eg:
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

#### Run tests
```bash
source activate hogwild-python 
py.test --color=yes
```
