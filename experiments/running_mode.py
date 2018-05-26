import os
import subprocess

RUNNING_MODE = ['synchronous', 'asynchronous']
N_WORKERS = 2
SCRIPT_PATH = os.path.join((os.sep)
                           .join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[0:-2]),
                           'hogwild-python/run-experiments.sh')
FILE_LOG = 'sync_async_7.json'

if __name__ == '__main__':
    for running_mode in RUNNING_MODE:
        subprocess.call('bash {} -n {} -r {} -f {} -w cluster'.format(SCRIPT_PATH,
                                                                      N_WORKERS, running_mode,
                                                                      FILE_LOG), shell=True)
