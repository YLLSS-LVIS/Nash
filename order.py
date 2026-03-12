class order:
    __slots__ = [
        "mpid",
        "contractID",
        "orderID",
        "price",
        "side",
        "qty",
        "head",
        "tail",
    ]

    def __init__(
        self, mpid, orderID, contractID, price, side, qty, head=None, tail=None
    ):
        self.mpid = mpid
        self.contractID = contractID
        self.orderID = orderID
        self.price = price
        self.side = side
        self.qty = qty
        self.head, self.tail = head, tail

    @property
    def is_head(self):
        if self.head is None:
            return True
        if self.head.price != self.price:
            return True
        return False

    def serialise_link(self, link):
        if link is None:
            return None
        return [link.mpid, link.orderID]

    def serialise(self):
        return [
            self.mpid,
            self.orderID,
            self.price,
            self.side,
            self.qty,
            self.serialise_link(self.head),
            self.serialise_link(self.tail),
        ]
