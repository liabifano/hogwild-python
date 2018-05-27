import os

LOCAL_PATH = os.path.join((os.sep)
                          .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                          'resources/rcv1')

# If testing locally, use localhost:port with different ports for each node/coordinator
# When running on different machines, can use the same port for all.
RUNNING_WHERE = os.environ.get('WHERE') if os.environ.get('WHERE') == 'cluster' else 'local'
DATA_PATH = os.environ.get('DATA_PATH') if os.environ.get('DATA_PATH') else LOCAL_PATH
N_WORKERS = os.environ.get('N_WORKERS')

coordinator_address = 'coordinator-roman-0.coordinator-service-roman:80' if RUNNING_WHERE != 'local' else 'localhost:50051'
worker_addresses = ['worker-roman-{}.workers-service-roman:80'.format(str(x)) for x in
                    range(int(N_WORKERS))] if RUNNING_WHERE != 'local' else ['localhost:50052', 'localhost:50053',
                                                                             'localhost:50054', 'localhost:50055']
                                                                             # 'localhost:50056', 'localhost:50057',
                                                                             # 'localhost:50058', 'localhost:50059',
                                                                             # 'localhost:50060', 'localhost:50061']
port = 80 if RUNNING_WHERE != 'local' else 50051

TRAIN_FILE = os.path.join(DATA_PATH, 'lyrl2004_vectors_train.dat') if DATA_PATH else ''
TOPICS_FILE = os.path.join(DATA_PATH, 'rcv1-v2.topics.qrels')
TEST_FILES = [os.path.join(DATA_PATH, x) for x in ['lyrl2004_vectors_test_pt0.dat',
                                                   'lyrl2004_vectors_test_pt1.dat',
                                                   'lyrl2004_vectors_test_pt2.dat',
                                                   'lyrl2004_vectors_test_pt3.dat']]

running_mode = os.environ.get('RUNNING_MODE') if os.environ.get('RUNNING_MODE') else 'synchronous'
synchronous = running_mode == 'synchronous'

learning_rate = 0.03 / len(worker_addresses)  # Learning rate for SGD
validation_split = 0.1  # Percentage of validation data
epochs = 100  # Number of training iterations over subset on each node
persistence = 15  # Abort if after so many epochs learning rate does not decrease
subset_size = 100  # Number of datapoints to train on each epoch
lambda_reg = 1e-5  # Regularization parameter
