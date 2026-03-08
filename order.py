class order:
    def __init__(self, mpid, contractID, price, side, qty):
        self.mpid = mpid
        self.contractID = contractID
        self.price = price
        self.side = side
        self.qty = qty
        self.head, self.tail = None, None
