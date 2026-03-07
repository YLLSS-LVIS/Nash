import numpy as np


class freeList:
    def __init__(self, length):
        self.freeSpots = np.array([i for i in range(0, length)], dtype=np.int32)
        self.status = np.zeros(length, dtype=np.bool)
        self.fetchIndex = length - 1

    def fetch_free_spot(self):
        idx = self.fetchIndex
        if idx < 0:
            return False

        return idx

    def occupy_free_spot(self):
        self.status[self.fetchIndex] = True
        self.fetchIndex -= 1

    def free_spot(self, idx):
        self.fetchIndex += 1
        self.status[idx] = False
        self.freeSpots[self.fetchIndex] = idx
