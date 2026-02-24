from sqlite3 import SQLITE_DETACH

from sortedcotainers import SortedDict


class MarginManager:
    def __init__(self, cost_function, user_balance, user_position):
        self.balance = user_balance
        self.cost_function = cost_function

        self.priceConverter = [-1, 1]
        self.priceLevels = [SortedDict(), SortedDict()]
        self.userPosition = user_position
        self.reduciblePosition = user_position[:]
        self.redLevels = [0, 0]
        self.tailRed = [None, None]

    # Remember that lower number means better price and higher number means worse price
    def add_order(self, price, side, qty):
        levels = self.priceLevels[side]
        price_lvl = price * self.priceConverter[side]
        tail_red = self.tailRed[side]

        # Spilt the order into reduce and increase components
        order_red = min(self.reduciblePosition[1 - side], qty)
        order_inc = qty - order_red
        margin_used = self.cost_function[side] * order_inc

        swaps = []
        scan_index = self.redLevels[side] - 1
        while True:
            # Check if there is no increase component
            if not order_inc:
                break

            # Check if there is no more price improvement possible
            if tail_red is None or tail_red <= price_lvl:
                break

            # It is now confirmed that price improvement is possible, i.e. the tail_red price is worse than the order price
            # Thus, the tail_red price is higher than the order price_lvl
            price_improvement = tail_red - price_lvl
            swap_level = levels[tail_red]
            swap_level_red = swap_level[0]
            swap_qty = min(order_inc, swap_level_red)
            if not swap_qty:
                break

            margin_used -= price_improvement * swap_qty

            swaps.append([tail_red, swap_level, swap_qty])
            if scan_index == 0:
                tail_red = None
                break

            scan_index -= 1
            tail_red = levels.keys()[scan_index]

        new_margin = self.balance[1] + margin_used
        if new_margin > self.balance[0]:
            return False

        self.balance[1] = new_margin

        red_levels = self.redLevels[side]
        for swap_price, swap_level, swap_qty in swaps:
            swap_level[0] -= swap_qty
            swap_level[1] += swap_qty
            if not swap_level[0]:
                red_levels -= 1
                del levels[swap_price]

        return True
