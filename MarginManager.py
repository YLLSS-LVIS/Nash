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

    def update_tail_red(self, side):
        side_red_levels = self.redLevels[side]
        if not side_red_levels:
            self.tailRed[side] = None
            return
        self.tailRed[side] = self.priceLevels[side].keys()[side_red_levels - 1]

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
            # If the swap quantity is not enough to deplete the entirety of the reduce component of the current price level being scanned,
            # it means that there is no further quantity to swap the entire increase component of the incoming order has been swapped
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

    def remove_order(self, price, side, qty):
        level_price = self.priceConverter[side] * price
        price_levels = self.priceLevels[side]
        level_qtys = price_levels[level_price]
        rmv_inc = min(qty, level_qtys[1])
        rmv_red = qty - rmv_inc
        if rmv_red > level_qtys[0]:
            raise Exception(
                "Fatal error: quantity exceeded that at position manager whilst attempting to remove an order. A desync muat have occurred."
            )

        prev_red = level_qtys[0]
        level_qtys[0] -= rmv_red
        level_qtys[1] -= rmv_inc

        if rmv_inc:
            self.balance[1] -= self.cost_function[side](price) * rmv_inc

        if prev_red and (not level_qtys[0]):
            self.redLevels[side] -= 1
            self.update_tail_red(side)

        if (not level_qtys[0]) and (not level_qtys[1]):
            del price_levels[level_price]

    def alloc_reducible(self, reducible_side):
        # What we want to do in this situation is to take the other side of the reducible position,
        # and starting from the worst reduce price, begin to allocate

        reducible_qty = self.reduciblePosition[reducible_side]
        alloc_side = [1, 0][reducible_side]
        alloc_levels = self.priceLevels[alloc_side]
        tail_red = self.tailRed[alloc_side]
        red_levels = self.redLevels[alloc_side]

        for i in range(self.redLevels[alloc_side] - 1, len(alloc_levels)):
            price_level, level_qtys = alloc_levels.peekitem(i)
            if not level_qtys[1]:
                continue

            alloc_qty = min(reducible_qty, level_qtys[1])
            if not alloc_qty:
                break

            prev_red = level_qtys[0]
            if not prev_red:
                tail_red = price_level
                red_levels += 1

            level_qtys[1] -= alloc_qty
            level_qtys[0] += alloc_qty
            norm_price = price_level * self.priceConverter[alloc_side]
            self.balance[1] -= self.cost_function[alloc_side](norm_price) * alloc_qty
            reducible_qty -= alloc_qty

        self.redLevels[alloc_side] = red_levels
        self.tailRed[alloc_side] = tail_red
        self.reduciblePosition[reducible_side] = reducible_qty
