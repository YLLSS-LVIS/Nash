class account:
    __slots__ = ["balance", "positions", "orders"]

    def __init__(self):
        self.balance = [0, 0]
        self.positions = set()
        self.orders = set()
