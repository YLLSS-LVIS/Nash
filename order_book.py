from sortedcontainers import SortedDict

from order import order
from position import position


class order_book:
    def __init__(self, _master, contract_id, max_resolution):
        self._master = _master
        self.globalAccounts = _master.accounts

        self.contract_id = contract_id
        self.max_resolution = int(max_resolution)
        self.cost_function = [lambda x: x, lambda x: self.max_resolution - x]

        self.levels = [SortedDict(), SortedDict()]
        self.price_converter = [-1, 1]

        self.linkedBooks = None
        self.linkedBookIndex = None

    def _add_order(self, order: order):
        order_price = order.price * self.price_converter[order.side]
        side_book = self.levels[order.side]
        if order_price in side_book:
            order_level = side_book[order_price]
            order_level[3].tail = order
            order_level[3] = order
            tail_level_price = order_level[1]
            if tail_level_price is not None:
                side_book[tail_level_price][2].head = order
            order_level[4] += 1
            order_level[5] += order.qty

    def _process_order(self):
        pass

    def post_order(self, mpid, price, side, qty):
        acct = self.globalAccounts[mpid]
        acct_positions = acct.positions
        if not len(acct.free_orders):
            return False  # All order slots used up

        pos_exists = True
        if self.contract_id not in acct_positions:
            pos_exists = False
            acct_positions[self.contract_id] = position(
                margin_function=self.cost_function,
                position=[0, 0],
                balance=acct.balance,
            )

        account_pos = acct_positions[self.contract_id]
        if account_pos.add_order(price, side, qty):
            new_order_id = acct.free_orders.pop(-1)
            new_order = order(
                orderID=new_order_id,
                mpid=mpid,
                contractID=self.contract_id,
                price=price,
                side=side,
                qty=qty,
            )

            acct.orders[new_order_id] = new_order
            self._process_order(self, order)
            return True

        return False  # Insufficient Margine
