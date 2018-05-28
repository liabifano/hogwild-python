from hogwild import settings

def generate_dictionary(datapoint):
    ''' Parses and generates a dictionary from one sparse datapoint. '''
    d = {0: 1.0} # Adding the bias
    for elem in datapoint:
        elem = elem.split(':')
        d[int(elem[0])] = float(elem[1])
    return d

def load_small_reuters_data():
    '''
    Used to load Reuters data from:
    https://archive.ics.uci.edu/ml/datasets/Reuters+RCV1+RCV2+Multilingual,+Multiview+Text+Categorization+Test+collection
    '''
    data = []
    labels = []
    with open(settings.RC_SMALL_TRAIN_PATH) as f:
        content = f.readlines()
        content = [line.strip() for line in content]
        content = [line.split(' ') for line in content]
        labels = [line[0] for line in content]
        data = [generate_dictionary(line[1:]) for line in content]
    return data, labels

def load_large_reuters_data(train_path, topics_path, test_path, selected_cat='CCAT', train=True):
    '''
    Used to load Reuters data from:
    http://www.ai.mit.edu/projects/jmlr/papers/volume5/lewis04a/lyrl2004_rcv1v2_README.htm
    '''
    data = []
    labels = []
    if train:
        with open(train_path) as f:
            content = f.readlines()
            content = [line.strip() for line in content]
            content = [line.split(' ') for line in content]
            labels = [int(line[0]) for line in content]
            data = [generate_dictionary(line[2:]) for line in content]
    else:
        paths = test_path
        for path in paths:
            with open(path) as f:
                content = f.readlines()
                content = [line.strip() for line in content]
                content = [line.split(' ') for line in content]
                labels_i = [int(line[0]) for line in content]
                data_i = [generate_dictionary(line[2:]) for line in content]
                labels = labels + labels_i
                data = data + data_i
    cat = get_category_dict(topics_path)
    labels = [1 if selected_cat in cat[label] else -1 for label in labels]
    return data, labels

def get_category_dict(topics_path):
    ''' Generates the category dictionary using the topics file from:
    http://www.ai.mit.edu/projects/jmlr/papers/volume5/lewis04a/lyrl2004_rcv1v2_README.htm
    '''
    categories = {}
    with open(topics_path) as f:
        content = f.readlines()
        content = [line.strip() for line in content]
        content = [line.split(' ') for line in content]
        for line in content:
            id = int(line[1])
            cat = line[0]
            if id not in categories:
                categories[id] = [cat]
            else:
                categories[id].append(cat)
    return categories

def train_val_split(data, targets, val_indices):
    ''' Split data into train and validation data using the given validation indices. '''
    data_train = [data[x] for x in range(len(targets)) if x not in val_indices]
    targets_train = [targets[x] for x in range(len(targets)) if x not in val_indices]
    data_val = [data[x] for x in val_indices]
    targets_val = [targets[x] for x in val_indices]
    return data_train, targets_train, data_val, targets_val
