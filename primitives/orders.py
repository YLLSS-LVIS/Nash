import array
from dataclasses import dataclass
from this import d


class orders:
    def __init__(self, alloc_size):
        self.max_orders = alloc_size
        self.free = array.array("L", [i for i in range(0, alloc_size)])
        self.used_orders = 0

        new_val = [0 for i in range(0, alloc_size)]
        self.mpid = array.array("L", new_val)
        self.order_id = array.array("L", new_val)
        self.contract_id = array.array("L", new_val)
        self.price = array.array("L", new_val)
        self.side = array.array("L", new_val)
        self.qty = array.array("L", new_val)
        self.head = array.array("L", new_val)
        self.tail = array.array("L", new_val)

    @property
    def space_available(self):
        return not self.used_orders == self.max_orders

    def add_order(self, mpid, order_id, contract_id, price, side, qty):
        idx = self.used_orders
        self.mpid[idx] = mpid
        self.order_id[idx] = order_id
        self.contract_id[idx] = contract_id
        self.price[idx] = price
        self.side[idx] = side
        self.qty[idx] = qty
        self.used_orders += 1

        return idx
