from position import position
from sortedcontainers import SortedDict


class order_book:
    def __init__(self, _master, contract_id, contract_max):
        self.contractID = int(contract_id)
        self.book = [SortedDict(), SortedDict()]
        self.price_levels = [self.book[0].keys(), self.book[1].keys()]
        self.tob = [None, None]

        self.accounts = _master.accounts
        self.maxSettlementValue = contract_max
        self.margin_function = [lambda x: x, lambda x: self.maxSettlementValue - x]

        self.userPositions = {}

        orders = _master.orders
        self.orders = orders
        self._remove_order = orders.remove_order
        self._add_order = orders.add_order
        self.mpid = orders.mpid
        self.order_id = orders.order_id
        self.contract_id = orders.contract_id
        self.price = orders.price
        self.side = orders.side
        self.qty = orders.qty
        self.head = orders.head
        self.tail = orders.tail
        self.in_use = orders.in_use

    def user_add_order(self, mpid, price, side, qty):
        if (
            price < 1
            or price >= self.maxSettlementValue
            or side not in [0, 1]
            or qty < 1
        ):
            return False

        first_timer = False
        acct = self.accounts[mpid]
        if mpid not in self.userPositions:
            first_timer = True

            user_position = position(
                margin_function=self.margin_function,
                position=[0, 0],
                balance=acct.balance,
            )
            self.userPositions[mpid] = user_position
            acct.positions.add(self.contractID)
        else:
            user_position = self.userPositions[mpid]

        if user_position.add_order(price, side, qty):
            new_order_id = self._add_order(mpid, self.contractID, price, side, qty)
            acct.orders.add(new_order_id)
        elif first_timer:
            acct.positions.remove(self.contractID)

    def process_aggressing_order(self, mpid, price, side, qty):
        acct_margin_manager = self.userPositions[mpid]
        order_price = [-1, 1][side] * price
        fill_qty = 0
        opp_side = [1, 0][side]
        # -bid >= offer
        # -offer >= bid
        while True:
            opp_tob = self.tob[opp_side]
            if opp_tob is None or -order_price < opp_tob or (not qty):
                break
            cur_fill = self.take_tob(opp_side, qty, mpid)
            fill_qty += cur_fill
            qty -= cur_fill
        acct_margin_manager.fill_order(price, side, abs(opp_tob), fill_qty)

    def take_tob(self, side, qty, mpid=None):
        # This section was written at TKTORC

        side_tob = self.tob[side]
        side_book = self.book[side]
        tob_lvl = side_book[side_tob]
        tob_order = tob_lvl[2]
        tob_orders, tob_qty = tob_lvl[4:6]
        filled_qty = 0
        for i in range(0, tob_orders):
            if tob_order == -1:
                break

            tob_order_mpid = self.mpid[tob_order]

            order_qty = self.qty[tob_order]
            if tob_order_mpid == mpid:
                order_qty = 0
            else:
                fill_qty = min(qty, order_qty)
                if not fill_qty:
                    break

                qty -= fill_qty
                filled_qty += fill_qty
                order_qty -= fill_qty
                tob_qty -= fill_qty

                order_price = self.price[tob_order]
                self.userPositions[tob_order_mpid].fill_order(
                    order_price, side, order_price, qty
                )

            if not order_qty:
                self._remove_order(tob_order)
                tob_orders -= 1
                tob_order = self.tail[tob_order]
            else:
                self.qty[tob_order] = order_qty

        if not tob_orders:
            self._book_remove_level(side, side_tob)
        else:
            tob_lvl[2] = tob_order
            tob_lvl[4:6] = tob_orders, tob_qty
        return filled_qty

    def fill_price_level(self, side, price_level, qty, mpid=None):
        # WARNING: This function is intended to fill the top-of-book ONLY. Using it otherwise will result in inconsistancies within related Account Position Managers.
        side_book = self.book[side]
        price_lvl = side_book[price_level]

    def _book_add_order(self, order_idx):
        order_price = self.price[order_idx]
        order_side = self.side[order_idx]
        order_qty = self.qty[order_idx]
        book_price = order_price * [-1, 1][order_side]
        side_book = self.book[order_side]
        price_levels = self.price_levels[order_side]

        if book_price in side_book:
            price_level = side_book[book_price]
            # prev_lvl_tail is the tail of the level with
            prev_lvl_tail = price_level[3]
            prev_lvl_tail_tail = self.tail[prev_lvl_tail]
            if prev_lvl_tail_tail != -1:
                self.head[prev_lvl_tail_tail] = order_idx
            self.tail[prev_lvl_tail] = order_idx
            self.head[order_idx] = prev_lvl_tail
            self.tail[order_idx] = prev_lvl_tail_tail
            price_level[4] += 1
            price_level[5] += order_qty

        else:
            price_level = [None, None, order_idx, order_idx, 1, order_qty]
            side_book[book_price] = price_level
            price_level_index = side_book.bisect_left(book_price)
            order_head, order_tail = -1, -1
            if price_level_index > 0:
                head_price = price_levels[price_level_index - 1]
                price_level[0] = head_price

                head_price_lvl = side_book[head_price]
                head_price_lvl[1] = book_price
                order_head = head_price_lvl[3]
                self.tail[order_head] = order_idx

            if price_level_index + 1 < len(price_levels):
                tail_price = price_levels[price_level_index + 1]
                price_level[1] = tail_price

                tail_price_lvl = side_book[tail_price]
                tail_price_lvl[0] = book_price
                order_tail = tail_price_lvl[2]
                self.head[order_tail] = order_idx

            self.head[order_idx] = order_head
            self.tail[order_idx] = order_tail

            tob = self.tob[order_side]
            if book_price < tob or tob is None:
                self.tob[order_side] = book_price

    def _book_remove_level(self, side, book_price):
        side_book = self.book[side]
        head_price, tail_price, head_order, tail_order, num_orders, qty = side_book[
            book_price
        ]
        if num_orders:
            raise Exception("Removal of price level containing orders attempted")
        if head_price is not None:
            side_book[head_price][1] = tail_price
        if tail_price is not None:
            side_book[tail_price][0] = head_price
        if not head_price:
            self.tob = tail_price
