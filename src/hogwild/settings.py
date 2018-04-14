import os

# Path to the English Reuters file
DATA_PATH = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1rcv2aminigoutte/EN/Index_EN-EN')

# If testing locally, use localhost:port with different ports for each node/coordinator
# When running on different machines, can use the same port for all.
port = '50051'
coordinator_address = 'localhost:' + port
node_addresses = ['localhost:50052', 'localhost:50053']

learning_rate = 1
test_percentage = 0.1
epochs = 100
batch_size = 100
lambda_reg=1e-5
