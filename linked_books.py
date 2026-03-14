class linked_books:
    def __init__(self, protocol_balance, contract_order_books):
        self.protocol_balance = protocol_balance

        self.books = [order_book for order_book in contract_order_books]

        # For aggr.buy orders (if total bids > maxSum then arb)
        self.maxSum = 0
        # For aggr.sell orders (if total offers < (minSum - totalUnoccopiedValue) then arb))
        self.minSum = 0

        self.totalUnoccupiedValue = sum(
            [order_book.maxResolution for order_book in contract_order_books]
        )
