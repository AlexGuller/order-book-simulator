class Order:
    def __init__(self, order_id, side, price, quantity):
        self.order_id = order_id
        self.side = side
        # Integer cents for limit orders; None for market orders.
        self.price = price
        self.quantity = quantity


class OrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []
        self.trades = []
        # Preserve accepted IDs even after orders fill or are canceled.
        self.used_order_ids = set()

    # Limit Orders
    def add_order(self, order):
        self.validate_order(order)
        self.used_order_ids.add(order.order_id)

        # Limit Buy
        if order.side == "buy":
            # Match the cheapest asks while they satisfy the buyer's limit.
            while (
                order.quantity > 0
                and self.asks
                and order.price >= self.asks[0].price
            ):
                seller = self.asks[0]

                # Neither order can trade more than its remaining quantity.
                traded_quantity = min(order.quantity, seller.quantity)
                order.quantity -= traded_quantity
                seller.quantity -= traded_quantity

                # Execute at the resting seller's price.
                self.trades.append({
                    "buy_order_id": order.order_id,
                    "sell_order_id": seller.order_id,
                    "price": seller.price,
                    "quantity": traded_quantity,
                })

                if seller.quantity == 0:
                    self.asks.pop(0)

            # Keep any unfilled quantity in the book.
            if order.quantity > 0:
                self.bids.append(order)
                # Stable sorting preserves arrival order at equal prices.
                self.bids.sort(key=lambda o: o.price, reverse=True)

        # Limit Sell
        elif order.side == "sell":
            # Match the highest bids while they satisfy the seller's limit.
            while (
                order.quantity > 0
                and self.bids
                and order.price <= self.bids[0].price
            ):
                buyer = self.bids[0]
                traded_quantity = min(buyer.quantity, order.quantity)
                buyer.quantity -= traded_quantity
                order.quantity -= traded_quantity

                # Execute at the resting buyer's price.
                self.trades.append({
                    "buy_order_id": buyer.order_id,
                    "sell_order_id": order.order_id,
                    "price": buyer.price,
                    "quantity": traded_quantity,
                })

                if buyer.quantity == 0:
                    self.bids.pop(0)

            if order.quantity > 0:
                self.asks.append(order)
                self.asks.sort(key=lambda o: o.price)

        else:
            raise ValueError("Side must be 'buy' or 'sell'")

    # Market Orders
    def add_market_order(self, order):
        self.validate_order(order, is_market=True)
        self.used_order_ids.add(order.order_id)

        # Market Buy: consume asks without a limit-price condition.
        if order.side == "buy":
            while self.asks and order.quantity > 0:
                seller = self.asks[0]
                traded_quantity = min(order.quantity, seller.quantity)
                order.quantity -= traded_quantity
                seller.quantity -= traded_quantity

                self.trades.append({
                    "buy_order_id": order.order_id,
                    "sell_order_id": seller.order_id,
                    "price": seller.price,
                    "quantity": traded_quantity,
                })

                if seller.quantity == 0:
                    self.asks.pop(0)

        # Market Sell: consume bids without a limit-price condition.
        elif order.side == "sell":
            while self.bids and order.quantity > 0:
                buyer = self.bids[0]
                traded_quantity = min(order.quantity, buyer.quantity)
                order.quantity -= traded_quantity
                buyer.quantity -= traded_quantity

                self.trades.append({
                    "buy_order_id": buyer.order_id,
                    "sell_order_id": order.order_id,
                    "price": buyer.price,
                    "quantity": traded_quantity,
                })

                if buyer.quantity == 0:
                    self.bids.pop(0)

        else:
            raise ValueError("Side must be 'buy' or 'sell'")

        # Any unfilled market quantity stays off the book.

    # Order Cancellation
    def remove_order(self, order_id):
        # Search both sides and remove only the remaining order.
        for orders in (self.bids, self.asks):
            for index, order in enumerate(orders):
                if order.order_id == order_id:
                    orders.pop(index)
                    return True
        return False

    # Order Validation
    def validate_order(self, order, is_market=False):
        if type(order.order_id) is not int or order.order_id <= 0:
            raise ValueError("Order ID must be a positive integer")

        if order.order_id in self.used_order_ids:
            raise ValueError("Order ID has already been used")

        if order.side not in ("buy", "sell"):
            raise ValueError("Side must be 'buy' or 'sell'")

        if type(order.quantity) is not int or order.quantity <= 0:
            raise ValueError("Quantity must be a positive integer")

        if is_market:
            if order.price is not None:
                raise ValueError("Market orders must use price=None")
        else:
            if type(order.price) is not int or order.price <= 0:
                raise ValueError("Price must be a positive integer in cents")

    # Depth Aggregation
    def get_depth(self, side):
        if side == "buy":
            orders = self.bids
        elif side == "sell":
            orders = self.asks
        else:
            raise ValueError("Side must be 'buy' or 'sell'")

        depth = {}
        # Combine remaining quantities from orders at the same price.
        for order in orders:
            depth[order.price] = depth.get(order.price, 0) + order.quantity

        return depth