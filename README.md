# Hogwild Python Implementation

HOGWILD! paper: https://arxiv.org/abs/1106.5730

(For the moment synchronous)

To generate the proto classes, run the following command inside the hogwild folder:
```
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. hogwild.proto
```

Configure the coordinator and worker locations in the settings.py file.

First run each node with the selected port number as an argument. Eg:
```
python node.py 50051
```

Then run the coordinator:
```
python coordinator.py
```
