class account:
    def __init__(self):
        self.balance = [0, 0]
        self.positions = {}
        self.orders = {}

    @property
    def avblOrderID(self):
        for i in range(0, 10):
            if i not in self.orders:
                return i
        return False
