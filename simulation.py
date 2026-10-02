import random

from order_book import Order, OrderBook


def run_simulation(num_steps=100):
    # Use a fresh random sequence each run.
    rng = random.Random(None)
    book = OrderBook()

    # Each step either cancels an order or submits a new one.
    for order_id in range(1, num_steps + 1):
        # Attempt cancellation on 10% of steps.
        if rng.random() < 0.1:
            resting_orders = book.bids + book.asks

            if resting_orders:
                order_to_cancel = rng.choice(resting_orders)
                book.remove_order(order_to_cancel.order_id)
                continue

        # If cancellation is unavailable, submit an order instead.
        side = rng.choice(["buy", "sell"])
        quantity = rng.randint(1, 20)

        # Of new submissions, 20% are market orders and 80% are limits.
        if rng.random() < 0.2:
            order = Order(order_id, side, None, quantity)
            book.add_market_order(order)
        else:
            # Limit prices range from $99.50 to $100.50 in integer cents.
            price = rng.randint(9950, 10050)
            order = Order(order_id, side, price, quantity)
            book.add_order(order)

    return book