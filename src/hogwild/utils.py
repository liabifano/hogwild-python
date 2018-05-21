import operator
import random
import socket

import numpy as np


def dotproduct(x, w):
    return sum([v * w[k] for k, v in x.items()])


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


def accuracy(labels, prediction):
    n_correct = sum([1 if l == p else 0 for l, p in zip(labels, prediction)])
    return n_correct / len(labels)


def split_dataset(data, target, k):
    total_size = len(data)
    positions = list(range(total_size))
    random.shuffle(positions)
    splits = np.array_split(positions, k)

    return [zip(list(operator.itemgetter(*s)(data)),
                list(operator.itemgetter(*s)(target)))
            for s in splits]


def ip(hostname, port):
    return '{}:{}'.format(socket.gethostbyname(hostname), port)
