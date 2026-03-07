import numpy as np


class orders:
    def __init__(self, max_orders):

        self.timestamp = np.zeros(max_orders, dtype=np.int32)
        self.mpid = np.zeros(max_orders, dtype=np.int32)
        self.price = np.zeros(max_orders, dtype=np.int16)
        self.side = np.zeros(max_orders, dtype=np.int8)
        self.qty = np.zeros(max_orders, dtype=np.int32)
        self.head = np.zeros(max_orders, dtype=np.int32)
        self.tail = np.zeros(max_orders, dtype=np.int32)
