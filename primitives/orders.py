import array


class orders:
    def __init__(self, alloc_size):
        self.max_orders = alloc_size
        self.free = array.array("L", [i for i in range(0, alloc_size)])
        self.used_orders = 0

        new_val = [0 for i in range(0, alloc_size)]
        self.mpid = array.array("L", new_val)
        self.order_id = array.array("L", [i for i in range(0, alloc_size)])
        self.contract_id = array.array("L", new_val)
        self.price = array.array("L", new_val)
        self.side = array.array("B", new_val)
        self.qty = array.array("L", new_val)
        self.head = array.array("L", new_val)
        self.tail = array.array("L", new_val)
        self.alive = array.array("B", new_val)

    @property
    def space_available(self):
        return not self.used_orders == self.max_orders

    def add_order(self, mpid, contract_id, price, side, qty):
        order_idx = self.used_orders
        self.alive[order_idx] = 1
        self.contract_id[order_idx] = contract_id
        self.price[order_idx] = price
        self.side[order_idx] = side
        self.qty[order_idx] = qty

    def remove_order(self, order_idx):
        if not self.alive[order_idx]:
            raise Exception("Removal of a dead order was attempted")

        order_head, order_tail = self.head[order_idx], self.tail[order_idx]
        if order_head != -1:
            self.tail[order_head] = order_tail
        if order_tail != -1:
            self.head[order_tail] = order_head
        self.alive[order_idx] = 0
        self.used_orders -= 1
        self.free[self.used_orders] = order_idx
