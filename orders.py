import numpy as np


class orders:
    def __init__(self, max_orders):

        self.timestamp = np.zeros(max_orders, dtype=np.int32)
        self.mpid = np.zeros(max_orders, dtype=np.int32)
