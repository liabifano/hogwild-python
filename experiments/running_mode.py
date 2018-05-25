import os

RUNNING_MODE = ['synchronous', 'asynchronous']
N_WORKERS = 7
THIS_PATH =
SCRIPT_PATH = os.path.join((os.sep)
                           .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                           'resources/rcv1')

if __name__ == '__main__':

