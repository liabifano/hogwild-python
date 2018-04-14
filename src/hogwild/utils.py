def dotproduct(x, w):
    return sum([v * w[k] for k,v in x.items()])

def sign(x):
    return 1 if x > 0 else -1 if x<0 else 0

def accuracy(labels, prediction):
    n_correct = sum([1 if l == p else 0 for l,p in zip(labels, prediction)])
    return n_correct / len(labels)
