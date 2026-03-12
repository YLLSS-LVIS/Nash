class linked_books:
    def __init__(self, contract_order_books):
        self.books = [order_book for order_book in contract_order_books]

        self.max_sum = 0
        self.min_sum = 0
        self.total_resolved_sum = 0

        self.max_offer_sum = -sum(
            order_book.res for order_book.maxResolution in contract_order_books
        )
