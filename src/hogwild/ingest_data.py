import settings

def generate_dictionary(datapoint):
    d = {0: 1.0} # for the bias
    for elem in datapoint:
        elem = elem.split(':')
        d[int(elem[0])] = float(elem[1])
    return d

def load_reuters_data():
    data = []
    labels = []

    with open(settings.DATA_PATH) as f:
        content = f.readlines()
        content = [line.strip() for line in content]
        content = [line.split(' ') for line in content]
        labels = [line[0] for line in content]
        data = [generate_dictionary(line[1:]) for line in content]

    return data, labels
