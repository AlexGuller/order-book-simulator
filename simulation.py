import random

from order_book import Order, OrderBook

#
def run_simulation(num_steps=100):
    rng = random.Random(None)
    book = OrderBook()
    
    for order_id in range(1, num_steps + 1):
        # 10% chance of canceling an existing order
        if rng.random() < .1:
            resting_orders = book.bids + book.asks
            
            if resting_orders:
                order_to_cancel = rng.choice(resting_orders)
                book.remove_order(order_to_cancel.order_id)
                continue
        
        side = rng.choice(["buy", "sell"])
        quantity = rng.randint(1, 20)
        
        # 20% chance of market order | 80% chance of limit order
        if rng.random() < .2:
            order = Order(order_id, side, None, quantity)
            book.add_market_order(order)
        else:
            price = rng.randint(9950, 10050)
            order = Order(order_id, side, price, quantity)
            book.add_order(order)
    return book

if __name__ == "__main__":
    book = run_simulation()

    print("Completed trades:", len(book.trades))
    print("Shares traded:", sum(t["quantity"] for t in book.trades))
    print("Remaining buy orders:", len(book.bids))
    print("Remaining sell orders:", len(book.asks))

    if book.bids:
        print(f"Best bid: ${book.bids[0].price / 100:.2f}")

    if book.asks:
        print(f"Best ask: ${book.asks[0].price / 100:.2f}")
        
    if book.bids and book.asks:
        best_bid = book.bids[0].price
        best_ask = book.asks[0].price

        spread = best_ask - best_bid
        midpoint = (best_bid + best_ask) / 2

        print(f"Spread: ${spread / 100:.2f}")
        print(f"Midpoint: ${midpoint / 100:.3f}")
        
    print("\nBID DEPTH")
    for price, quantity in book.get_depth("buy").items():
        print(f"${price / 100:.2f}: {quantity} shares")

    print("\nASK DEPTH")
    for price, quantity in book.get_depth("sell").items():
        print(f"${price / 100:.2f}: {quantity} shares")