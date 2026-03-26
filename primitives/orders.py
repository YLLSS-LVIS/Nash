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
        self.in_use = array.array("B", new_val)

    @property
    def space_available(self):
        return not self.used_orders == self.max_orders
