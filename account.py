class account:
    def __init__(self):
        self.balance = [0, 0]
        self.positions = {}
        self.orders = {}
        self.free_orders = [i for i in range(0, 20)]
