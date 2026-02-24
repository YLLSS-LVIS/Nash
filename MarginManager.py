from sortedcontainers import SortedDict


class MarginManager:
    def __init__(self, cost_function, user_balance, user_position):
        self.cost_function = cost_function
        self.priceConverter = [-1, 1]

        self.balance = user_balance
        self.userPosition = user_position
        self.reduciblePosition = user_position[:]

        self.priceLevels = [SortedDict(), SortedDict()]

        self.redLevels = [0, 0]
        self.tailRed = [None, None]

    # Remember that lower number means better price and higher number means worse price
    def add_order(self, price, side, qty):
        price_levels = self.priceLevels[side]
        order_price = price * self.priceConverter[side]
        tail_red = self.tailRed[side]

        # Spilt the order into reduce and increase components
        order_red = min(self.reduciblePosition[1 - side], qty)
        order_inc = qty - order_red
        margin_used = self.cost_function[side] * order_inc

        swaps = []
        # Remember that scan_index is the worst reduce level at the moment (lowest bid or highest offer)
        scan_index = self.redLevels[side] - 1
        while True:
            # Check if there is no increase component
            if not order_inc:
                break

            # Check if there is no more price improvement possible
            if tail_red is None or tail_red <= order_price:
                break

            # It is now confirmed that price improvement is possible, i.e. the tail_red price is worse than the order price
            # Thus, the tail_red price is higher than order_price
            price_improvement = tail_red - order_price
            swap_level = price_levels[tail_red]
            swap_level_red = swap_level[0]
            swap_qty = min(order_inc, swap_level_red)
            if not swap_qty:
                break

            order_red += swap_qty
            order_inc -= swap_qty
            margin_used -= price_improvement * swap_qty
            swaps.append([tail_red, swap_level, swap_qty])

            # If we have swapped over all reduce quantities of the swap level, we have to update scan_index and tail_red accordingly.
            if swap_qty == swap_level_red:
                if scan_index == 0:
                    tail_red = None
                    break
                scan_index -= 1
                tail_red = price_levels.keys()[scan_index]
            else:
                break

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
                del price_levels[swap_price]

        if order_price not in price_levels:
            price_levels[order_price] = [order_red, order_inc]
            if order_red:
                red_levels += 1
                if tail_red is None or order_price > tail_red:
                    tail_red = order_price
        else:
            price_level_qtys = price_levels[order_price]
            old_red = price_level_qtys[0]
            price_level_qtys[0] += order_red
            price_level_qtys[1] += order_inc
            if (not old_red) and order_red:
                red_levels += 1
                if tail_red is None or order_price > tail_red:
                    tail_red = order_price

        self.redLevels[side] = red_levels
        self.tailRed[side] = tail_red

        return True
