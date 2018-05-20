import os
import yaml
import argparse


WORKER_PATH = os.path.join(os.path.abspath(os.path.join(__file__, '..')), 'workers.yaml')
COORDINATOR_PATH = os.path.join(os.path.abspath(os.path.join(__file__, '..')), 'coordinator.yaml')

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('--n-workers', type=int, default=5)
parser.add_argument('--data-path', type=str, default='data/dataset')
parser.add_argument('--asynchronous', action="store_true", default=False)
args = vars(parser.parse_args())


if __name__ == '__main__':
    with open(WORKER_PATH) as f:
        workers = yaml.load(f)

    with open(COORDINATOR_PATH) as f:
        coordinator = yaml.load(f)

    n_workers = args['n_workers']
    data_path = args['data_path']
    running_mode = 'asynchronous' if args['asynchronous'] else 'synchronous'

    workers['spec']['replicas'] = n_workers
    env = workers['spec']['template']['spec']['containers'][0]['env']
    env_mod = [{'name': x['name'], 'value': n_workers} if x['name'] == 'N_WORKERS' else x for x in env]
    env_mod = [{'name': x['name'], 'value': running_mode} if x['name'] == 'RUNNING_MODE' else x for x in env_mod]
    env_mod = [{'name': x['name'], 'value': data_path} if x['name'] == 'DATA_PATH' else x for x in env_mod]
    workers['spec']['template']['spec']['containers'][0]['env'] = env_mod

    env = coordinator['spec']['template']['spec']['containers'][0]['env']
    env_mod = [{'name': x['name'], 'value': n_workers} if x['name'] == 'N_WORKERS' else x for x in env]
    env_mod = [{'name': x['name'], 'value': running_mode} if x['name'] == 'RUNNING_MODE' else x for x in env_mod]
    env_mod = [{'name': x['name'], 'value': data_path} if x['name'] == 'DATA_PATH' else x for x in env_mod]
    coordinator['spec']['template']['spec']['containers'][0]['env'] = env_mod

    # print(workers)

    # import pdb; pdb.set_trace()