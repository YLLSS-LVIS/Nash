from orders import orders


class Nash:
    def __init__(self):
        self.accounts = {}
        self.contracts = {}
        self.orders = orders(1_000_000)

    def place_order(self, mpid, contractID, price, side, qty):
        contractID = int(contractID)

        if not mpid in self.accounts:
            return False
        if not contractID in self.accounts:
            return False

        return self.contracts[contractID].add_order(mpid, price, side, qty)

    def cancel_order(self, mpid, order_id):
        pass
