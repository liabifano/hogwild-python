from hogwild.utils import dotproduct, sign


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

    def fit(self, data, labels):
        total_delta_w = {}

        for x, label in zip(data, labels):
            if self.__misclassification(x, label):
                delta_w = self.__gradient(x, label)
                self.update_weights(delta_w)
            else:
                delta_w = self.__regularization_gradient(x)
                self.update_weights(delta_w)
            for k, v in delta_w.items():
                if k in total_delta_w:
                    total_delta_w[k] += v
                else:
                    total_delta_w[k] = v
        return total_delta_w

    def __loss(self, data, labels):
        total_loss = 0
        for x, label in zip(data, labels):
            wx = dotproduct(x, self.__w)
            total_loss += max(1 - label * wx, 0)
            total_loss += __regularizer(x)
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

    def __misclassification(self, x, label):
        return dotproduct(x, self.__w) * label < 1

    def update_weights(self, delta_w):
        for k, v in delta_w.items():
            self.__w[k] += self.__getLearningRate() * v

    def predict(self, data):
        return [sign(dotproduct(x, self.__w)) for x in data]
