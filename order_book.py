from sortedcontainers import SortedDict

from order import order
from position import position


class order_book:
    def __init__(self, _master, contractID, maxResolution):
        self._master = _master
        self.globalAccounts = _master.accounts

        self.contractID = contractID
        self.maxResolution = int(maxResolution)
        self.cost_function = [lambda x: x, lambda x: self.maxResolution - x]

        self.levels = [SortedDict(), SortedDict()]
        self.priceLevels = [self.levels[0].keys(), self.levels[1].keys()]
        self.topOfBook = [None, None]
        self.price_converter = [-1, 1]

        self.linkedBooks = None
        self.linkedBookIndex = None

    def _add_order(self, order: order):
        """
        Adds a new order into the order book, returns the change in the form of (level_presence_change, level_tob_change)
        """
        price_converter = self.price_converter[order.side]

        order_price = order.price * price_converter
        side_book = self.levels[order.side]
        side_price_levels = self.priceLevels[order.side]

        tob_change = 0
        free_total_change = 0
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
                tob_change = order.price
                free_total_change = -self.maxResolution
            else:
                new_order_diff = tob - order_price
                if new_order_diff > 0:  # New level is top-of-book
                    tob_change = new_order_diff
                    tob = new_order_diff
            self.topOfBook[order.side] = tob
        return tob_change, free_total_change

    def _remove_order(self, order: order):
        _converter = self.price_converter[order.side]
        order_price = order.price * _converter
        side_book = self.levels[order.side]

        # Handle processing of order linked list
        if order.head is not None:
            order.head.tail = order.tail
        if order.tail is not None:
            order.tail.head = order.head

        order_level = side_book[order_price]
        head_price, tail_price = order_level[0:2]
        order_level[4] -= 1
        if not order_level[4]:
            return self._remove_level(order.side, _converter * order.price)

    def _remove_level(self, side, price):
        _converter = self.price_converter[side]
        side_levels = self.levels[side]
        price_level = side_levels[price]

        price_level_head, price_level_tail = price_level[0:3]
        head_exists = price_level_head is not None
        tail_exists = price_level_tail is not None
        tob_change, free_total_change = 0, 0

        if head_exists:
            side_levels[price_level_head][1] = price_level_tail
        if tail_exists:
            side_levels[price_level_tail][0] = price_level_head

        # If the price level has no tail, it is the TOB (top-of-book)
        if not (
            head_exists + tail_exists
        ):  # The TOB is also the only price level on the specified side
            tob_change = price * -_converter
            free_total_change = self.maxResolution
            self.topOfBook[side] = None
        elif not head_exists:  # There is a second-best price level after the TOB
            # price_level_tail * price must be positive, and the change of TOB should be negative for the bid side and positive for the offer side
            tob_change = price_level_tail * price * _converter
            self.topOfBook[side] = price_level_tail
        del side_levels[price]
        return tob_change, free_total_change

    def lift_tob(self, side, qty):
        tob = self.topOfBook[side]
        if tob is None:
            raise Exception("No top-of-book exists for the specified side")
        side_levels = self.levels[side]
        tob_level = side_levels[tob]
        if qty > tob_level[5]:
            raise Exception("Requested fill exceeded top-of-book quantity")

        tob_level[5] -= qty
        num_orders = tob_level[4]
        while True:
            tob_order = tob_level[2]
            fill_qty = min(qty, tob_order.qty)
            self.fill_order(tob_order, tob_order.price, fill_qty)
            if not tob_order.qty:
                if tob_order.tail is not None:
                    tob_order.tail.head = None
                num_orders -= 1
            qty -= fill_qty
            tob_level[5] -= qty
            if (not fill_qty) or (not num_orders):
                break
            # We only set the tail after the tob level is changed, to ensure that there is no redundant operation with changes to a level that is about to be removed
            tob_level[2] = tob_order.tail

        _converter = self.price_converter[side]
        if not num_orders:
            return self._remove_level(side, tob)

    def fill_order(self, order: order, price, qty):
        margin_manager = self.globalAccounts[order.mpid].positions[order.contractID]
        margin_manager.fill_order(order.price, order.side, price, qty)
        order.qty -= qty

    def _process_order(self, order):
        pass

    def post_order(self, mpid, price, side, qty):
        acct = self.globalAccounts[mpid]
        acct_positions = acct.positions
        new_order_id = acct.avblOrderID
        if new_order_id is None:
            return False  # All order slots used up

        pos_exists = True
        if self.contractID not in acct_positions:
            pos_exists = False
            acct_positions[self.contractID] = position(
                margin_function=self.cost_function,
                position=[0, 0],
                balance=acct.balance,
            )

        account_pos = acct_positions[self.contractID]
        if account_pos.add_order(price, side, qty):
            new_order = order(
                orderID=new_order_id,
                mpid=mpid,
                contractID=self.contractID,
                price=price,
                side=side,
                qty=qty,
            )

            acct.orders[new_order_id] = new_order
            self._process_order(order)
            return True
        if not pos_exists:
            del acct_positions[self.contractID]
        return False  # Insufficient Margin
