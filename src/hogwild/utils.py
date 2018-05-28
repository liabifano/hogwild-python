import operator
import random
import socket
import numpy as np

def dotproduct(x, w):
    ''' Calculates the dotproduct for sparse x and w. '''
    return sum([v * w[k] for k, v in x.items()])

def sign(x):
    ''' Sign function '''
    return 1 if x > 0 else -1 if x < 0 else 0

def accuracy(labels, prediction):
    ''' Returns the total accuracy of the predictions with the true labels '''
    n_correct = sum([1 if l == p else 0 for l, p in zip(labels, prediction)])
    return n_correct / len(labels)

def calculate_accs(targets, predictions):
    ''' Calculates separately the total accuracy and accuracies for each category. '''
    # Calculate accuracy of label 1
    a = sum([1 for x in zip(targets, predictions) if x[0] == 1 and x[1] == 1])
    b = sum([1 for x in targets if x == 1])
    acc_pos = a / b
    # Calculate accuracy of label -1
    c = sum([1 for x in zip(targets, predictions) if x[0] == -1 and x[1] == -1])
    d = sum([1 for x in targets if x == -1])
    acc_neg = c / d
    # Overall accuracy
    acc_tot = accuracy(targets, predictions)
    return acc_pos, acc_neg, acc_tot
