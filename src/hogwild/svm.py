from hogwild.utils import dotproduct, sign
from hogwild import ingest_data
import multiprocessing
import random
from hogwild import settings as s
from hogwild import hogwild_pb2, hogwild_pb2_grpc
import grpc


class SVM:
    def __init__(self, learning_rate, lambda_reg, dim):
        self.__learning_rate = learning_rate
        self.__lambda_reg = lambda_reg
        self.__dim = dim
        self.__w = [0.0] * dim

    def __getLearningRate(self):
        return self.__learning_rate

    def __getRegLambda(self):
        return self.__lambda_reg

    def __getDim(self):
        return self.__dim

    def __getW(self):
        return self.__w

    # TODO: Comment update flag. (if synch, do not update, since then coord would need to not send back specific update)
    def fit(self, data, labels, update=True):
        total_delta_w = {}
        train_loss = 0
        for x, label in zip(data, labels):
            xw = dotproduct(x, self.__w)
            if self.__misclassification(xw, label):
                delta_w = self.__gradient(x, label)
                if update:
                    self.update_weights(delta_w)
            else:
                delta_w = self.__regularization_gradient(x)
                if update:
                    self.update_weights(delta_w)
            for k, v in delta_w.items():
                if k in total_delta_w:
                    total_delta_w[k] += v
                else:
                    total_delta_w[k] = v
            train_loss += max(1 - label * xw, 0)
            train_loss += self.__regularizer(x)
        return total_delta_w, train_loss

    def loss(self, data, labels):
        total_loss = 0
        for x, label in zip(data, labels):
            xw = dotproduct(x, self.__w)
            total_loss += max(1 - label * xw, 0)
            total_loss += self.__regularizer(x)
        return total_loss

    def __regularizer(self, x):
        w = self.__getW()
        return self.__getRegLambda() * sum([w[i]**2 for i in x.keys()]) / len(x)

    def __regularizer_g(self, x):
        w = self.__getW()
        return 2 * self.__getRegLambda() * sum([w[i] for i in x.keys()]) / len(x)

    def __gradient(self, x, label):
        regularizer = self.__regularizer_g(x)
        return {k: (v * label - regularizer) for k, v in x.items()}

    def __regularization_gradient(self, x):
        regularizer = self.__regularizer_g(x)
        return {k: regularizer for k in x.keys()}

    def __misclassification(self, x_dot_w, label):
        return x_dot_w * label < 1

    def update_weights(self, delta_w):
        for k, v in delta_w.items():
            self.__w[k] += self.__getLearningRate() * v

    def predict(self, data):
        return [sign(dotproduct(x, self.__w)) for x in data]


def svm_subprocess(task_queue, response_queue, val_indices):
    print('Loading training data')
    data, targets = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                        s.TOPICS_FILE,
                                                        s.TEST_FILES,
                                                        selected_cat='CCAT',
                                                        train=True)
    data_train = [data[x] for x in range(len(targets)) if x not in val_indices]
    targets_train = [targets[x] for x in range(len(targets)) if x not in val_indices]
    data_val = [data[x] for x in val_indices]
    targets_val = [targets[x] for x in val_indices]
    print('Number of train datapoints: {}'.format(len(targets_train)))
    print('Number of validation datapoints: {}'.format(len(targets_val)))

    dim = max([max(k) for k in data]) + 1
    svm = SVM(learning_rate=s.learning_rate, lambda_reg=s.lambda_reg, dim=dim)

    while True:
        next_task = task_queue.get()
        if next_task is None:
            # Poison pill means shutdown
            print('SVM subprocess got poison pill. Exiting from subprocess.')
            break

        # Tasks are dictionaries: {'type': 'foo', 'payload': bar}
        task_type = next_task['type']
        if task_type == 'calculate_svm_update':
            # Select random subset
            subset_indices = random.sample(range(len(targets_train)), s.subset_size)
            data_stoc = [data_train[x] for x in subset_indices]
            targets_stoc = [targets_train[x] for x in subset_indices]
            # Calculate weight updates
            total_delta_w, train_loss = svm.fit(data_stoc, targets_stoc, update=not s.synchronous) # TODO: add train loss term
            response_queue.put({'total_delta_w': total_delta_w, 'train_loss': train_loss})

            # TODO: Send train loss to coordinator (with id?)

        elif task_type == 'update_weights':
            svm.update_weights(next_task['all_delta_w'])


        elif task_type == 'calculate_val_loss':
            val_loss = svm.loss(data_val, targets_val)
            response_queue.put(val_loss)


        elif task_type == 'predict':
            values = next_task['values']
            preds = svm.predict(values)
            response_queue.put(preds)
