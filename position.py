from sortedcontainers import SortedDict


class position:
    def __init__(self, margin_function, position, balance):
        self.balance = balance
        self.position = position
        self.reducible = position[:]

        self.priceLevels = [SortedDict(), SortedDict()]
        self.priceKeys = [self.priceLevels[0].keys(), self.priceLevels[1].keys()]

        self.redLevels = [0, 0]
        self.incLevels = [0, 0]

        self.price_converter = [-1, 1]
        self.opposite_side = [1, 0]
        self.margin_function = margin_function

    def add_order(self, price, side, qty):
        order_price = self.price_converter[side] * price
        order_red = min(qty, self.reducible[self.opposite_side[side]])
        order_inc = qty - order_red
        margin_used = self.margin_function[side][price]

        price_levels = self.priceLevels[side]
        red_levels = self.redLevels[side]
        swaps = []
        for i in range(red_levels - 1, -1, -1):
            if not order_inc:
                break
            level_price, level_qtys = price_levels.peekitem(index=i)
            if order_price >= level_price:
                break

            swap_qty = min(level_qtys[0], order_inc)
            swaps.append([level_price, level_qtys, swap_qty])

            order_inc -= swap_qty
            order_red += swap_qty
            margin_used -= (level_price - price) * swap_qty

        new_margin = self.balance[1] + margin_used
        if new_margin > self.balance[0]:
            return False

        inc_levels = self.incLevels[side]
        for level_price, level_qtys, swap_qty in swaps:
            old_red, old_inc = level_qtys

            level_qtys[0] -= swap_qty
            level_qtys[1] += swap_qty

            if (old_red) and (not level_qtys[0]):
                red_levels -= 1
            if not old_inc:
                inc_levels += 1

        if order_price not in price_levels:
            price_levels[order_price] = [order_red, order_inc]
            if order_red:
                red_levels += 1
            if order_inc:
                inc_levels += 1
        else:
            level = price_levels[order_price]
            old_red, old_inc = level

            level[0] += order_red
            level[1] += order_inc

            if (not old_red) and order_red:
                red_levels += 1
            if (not old_inc) and order_inc:
                inc_levels += 1

        self.redLevels[side] = red_levels
        self.incLevels[side] = inc_levels

    def alloc_reducible(self, side):
        reducible = self.reducible[side]

        opposite_side = self.opposite_side[side]

        alloc_levels = self.priceLevels[opposite_side]
        inc_levels = self.incLevels[opposite_side]
        red_levels = self.redLevels[opposite_side]

        margin_used = self.balance[1]
        for i in range(-inc_levels, 0):
            price, level_qtys = alloc_levels.peekitem(i)
            old_red, old_inc = level_qtys
            alloc_qty = min(old_inc, reducible)
            if not alloc_qty:
                break

            level_qtys[1] -= alloc_qty
            level_qtys[0] += alloc_qty

            margin_used -= self.margin_function[opposite_side](
                price * self.price_converter[opposite_side]
            )
            if not old_red:
                red_levels += 1
            if old_inc == alloc_qty:
                inc_levels -= 1

        self.redLevels[opposite_side] = red_levels
        self.incLevels[opposite_side] = inc_levels

    def remove_order(self, price, side, qty):
        level_price = self.price_converter[side] * price
        price_levels = self.priceLevels[side]
        level_qtys = price_levels[level_price]

        rmv_inc = min(level_qtys[1], qty)
        rmv_red = qty - rmv_inc
        if rmv_red > level_qtys[0]:
            raise Exception("Fatal error: overflow during order removal process")

        old_red, old_inc = level_qtys

        level_qtys[0] -= rmv_red
        level_qtys[1] -= rmv_inc

        if old_red and (not level_qtys[0]):
            self.redLevels[side] -= 1
        if old_inc and (not level_qtys[1]):
            self.incLevels[side] -= 1

        if rmv_red:
            opposite_side = self.opposite_side[side]
            self.reducible[opposite_side] += rmv_red
            self.alloc_reducible(opposite_side)

        if not sum(level_qtys):
            del price_levels[level_price]

    def fill_order(self, order_price, order_side, fill_price, fill_qty):
        level_price = self.price_converter[order_price] * order_price
        price_levels = self.priceLevels[order_side]
        level_qtys = price_levels[level_price]

        fill_red = min(fill_qty, level_qtys[0])
        fill_inc = fill_qty - fill_red
        if fill_inc > level_qtys[1]:
            raise Exception(
                "Fatal error: fill exceeded total quantity at maker order price level in position manager"
            )

        self.balance[1] -= self.margin_function[order_side](order_price) * fill_inc
        self.balance[0] -= self.margin_function[order_side](fill_price) * fill_inc

        sale_revenue = self.margin_function[self.opposite_side[order_side]] * fill_red
        self.balance[0] += sale_revenue
        self.balance[1] += sale_revenue

        old_red, old_inc = level_qtys
        level_qtys[0] -= fill_red
        level_qtys[1] -= fill_inc

        if old_red and (not level_qtys[0]):
            self.redLevels[order_side] -= 1
        if old_inc and (not level_qtys[1]):
            self.incLevels[order_side] -= 1
