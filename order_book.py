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
        self.priceLevels = [self.levels[0].keys(), self.levels[1].keys()]
        self.topOfBook = [None, None]
        self.price_converter = [-1, 1]

        self.linkedBooks = None
        self.linkedBookIndex = None

    def _add_order(self, order: order):
        """
        Adds a new order into the order book, returns the change in the form of (level_presence_change, level_price_change)
        """
        price_converter = self.price_converter[order.side]

        order_price = order.price * price_converter
        side_book = self.levels[order.side]
        side_price_levels = self.priceLevels[order.side]

        price_change = 0
        side_change = 0
        if order_price in side_book:
            order_level = side_book[order_price]
            order_level[3].tail = order
            order_level[3] = order
            tail_level_price = order_level[1]
            if tail_level_price is not None:
                side_book[tail_level_price][2].head = order
            order_level[4] += 1
            order_level[5] += order.qty
        else:
            new_level = [None, None, order, order, 1, order.qty]
            side_book[order_price] = new_level
            new_level_idx = side_price_levels.index(order_price)
            if new_level_idx > 0:
                head_price, head_price_level = side_book.peekitem(new_level_idx - 1)
                head_price_level[3].tail = order
                new_level[0] = head_price
            if new_level_idx < len(side_price_levels) - 1:
                tail_price, tail_price_level = side_book.peekitem(new_level_idx + 1)
                tail_price_level[2].head = order
                new_level[1] = tail_price
            tob = self.topOfBook[order.side]
            if tob is None:
                tob = order_price
                price_change = order_price * price_converter
                side_change = 1
            else:
                new_order_diff = tob - order_price
                if new_order_diff > 0:  # New level is top-of-book
                    price_change = new_order_diff * -price_converter
                    tob = new_order_diff
            self.topOfBook[order.side] = tob
        return side_change, price_change

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
