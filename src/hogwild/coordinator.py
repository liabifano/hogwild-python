import utils
import settings as s
import ingest_data
from svm import SVM
from node import HogwildServicer
from concurrent import futures
import grpc
import time
import sys
import random

# Import the automatically generated classes
import hogwild_pb2
import hogwild_pb2_grpc

# Step 1: Load the data from the reuters dataset and create targets
print('Data path:', s.DATA_PATH)
data, labels = ingest_data.load_reuters_data()
targets = [1 if x in ['ECAT', 'CCAT', 'M11'] else -1 for x in labels]
print('Number of datapoints: {}'.format(len(targets)))
print('Labels: {}'.format(set(labels)))

# Split into train and test datasets
test_indices = random.sample(range(len(targets)), int(0.1 * len(targets)))
data_train = [data[x] for x in range(len(targets)) if x not in test_indices]
targets_train = [targets[x] for x in range(len(targets)) if x not in test_indices]
data_test = [data[x] for x in test_indices]
targets_test = [targets[x] for x in test_indices]

# Step 2: Startup the nodes
# addresses of all nodes and coordinator and the dataset to all worker nodes
stubs = {}
for node_addr in s.node_addresses:
    # Open a gRPC channel
    channel = grpc.insecure_channel(node_addr, options=[('grpc.max_message_length',1024*1024*1024),\
                                                        ('grpc.max_send_message_length',1024*1024*1024),\
                                                        ('grpc.max_receive_message_length',1024*1024*1024)])
    # Create a stub (client)
    stub = hogwild_pb2_grpc.HogwildStub(channel)
    stubs[node_addr] = stub
    # Send to each node the list of all other nodes and the coordinator
    other_nodes = s.node_addresses.copy()
    other_nodes.remove(node_addr)
    info = hogwild_pb2.NetworkInfo(coordinator_address=s.coordinator_address, node_addresses=other_nodes)
    response = stub.GetNodeInfo(info)
    # Send the whole dataset to all the workers
    print('Sending dataset to node at {}'.format(node_addr))
    dataset = hogwild_pb2.DataSet()
    for dp, t in zip(data_train, targets_train):
        dp_i = dataset.datapoints.add()
        for k,v in dp.items():
            dp_i.datapoint[k] = v
        dp_i.target = t
    response = stub.GetDataSet(dataset)


# Step 3: Create a listener for the coordinator and send start command to all nodes
# Create a gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# Use the generated function `add_HogwildServicer_to_server`
# to add the defined class to the created server
hws = HogwildServicer()
hogwild_pb2_grpc.add_HogwildServicer_to_server(hws, server)

# Listen on port defined in settings.py
print('Starting coordinator server. Listening on port {}.'.format(s.port))
server.add_insecure_port('[::]:{}'.format(s.port))
server.start()

# Send start message to all the nodes
for stub in stubs.values():
    start = hogwild_pb2.StartMessage(learning_rate=s.learning_rate,
                                     lambda_reg=s.lambda_reg,
                                     epochs=s.epochs,
                                     batch_size=s.batch_size)
    response = stub.StartSGD(start)
print('Start message sent to all nodes. SGD running...')

# Wait until SGD done and calculate prediction
try:
    while hws.epochs_done != len(s.node_addresses):
        time.sleep(1)
    print('All SGD epochs done!')
    dim = max([max(k) for k in data]) + 1
    hws.svm = SVM(learning_rate=s.learning_rate, lambda_reg=s.lambda_reg, dim=dim)

    hws.svm.update_weights(hws.all_delta_w)
    prediction = hws.svm.predict(data_test)
    a = sum([1 for x in zip(targets_test, prediction) if x[0] == 1 and x[1] == 1])
    b = sum([1 for x in targets_test if x == 1])
    print('Test accuracy of Label 1: {:.2f}%'.format(a/b))

    c = sum([1 for x in zip(targets_test, prediction) if x[0] == -1 and x[1] == -1])
    d = sum([1 for x in targets_test if x == -1])
    print('Test accuracy of Label -1: {:.2f}%'.format(c/d))
    print('Test accuracy: {:.2f}%'.format(utils.accuracy(targets_test, prediction)))
except KeyboardInterrupt:
    server.stop(0)
