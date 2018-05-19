import math

class EarlyStopping():
    def __init__(self, persistence):
        self.persistence = persistence
        self.window = []
        self.window_smallest = math.inf

    def stopping_criterion(self, current_loss):
        window_size = len(self.window)
        if window_size == self.persistence:
            del self.window[0]
        self.window.append(current_loss)
        if min(self.window) > self.window_smallest:
            return True
        self.window_smallest = min(self.window)
        return False
