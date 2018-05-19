import os

# Path to the small English Reuters file
RC_SMALL_TRAIN_PATH = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1rcv2aminigoutte/EN/Index_EN-EN')

# Path to the Large Reuters file
RC_LARGE_TRAIN_PATH = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/lyrl2004_vectors_train.dat')
RC_LARGE_LABELS_PATH = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/rcv1-v2.topics.qrels')
RC_LARGE_TEST_PATH0 = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/lyrl2004_vectors_test_pt0.dat')
RC_LARGE_TEST_PATH1 = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/lyrl2004_vectors_test_pt1.dat')
RC_LARGE_TEST_PATH2 = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/lyrl2004_vectors_test_pt2.dat')
RC_LARGE_TEST_PATH3 = os.path.join((os.sep)
                         .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                         'resources/rcv1/lyrl2004_vectors_test_pt3.dat')

# If testing locally, use localhost:port with different ports for each node/coordinator
# When running on different machines, can use the same port for all.
coordinator_port = '50051'
coordinator_address = 'localhost:{}'.format(coordinator_port)
node_addresses = ['localhost:50052', 'localhost:50053', 'localhost:50054']

# TODO: Temporary. Set flag with startup...
synchronous = False # Synchronous or asynchronous mode selection

learning_rate = 0.01 # Learning rate for SGD
validation_split = 0.1 # Percentage of validation data
epochs = 1000 # Number of training iterations over subset on each node
persistence = 20 # Abort if after so many epochs learning rate does not decrease
subset_size = 100 # Number of datapoints to train on each epoch
lambda_reg = 1e-5 # Regularization parameter
