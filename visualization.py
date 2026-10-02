import matplotlib.pyplot as plt

from simulation import run_simulation


def plot_order_book(book):
    # Combine remaining order quantities at each price.
    bids = book.get_depth("buy")
    asks = book.get_depth("sell")

    fig, ax = plt.subplots()

    # Convert cents to dollars; bar lengths represent available shares.
    # A height of $0.008 leaves gaps between $0.01 price levels.
    ax.barh(
        [price / 100 for price in bids],
        list(bids.values()),
        height=0.008,
        color="green",
        label="Bids",
    )

    ax.barh(
        [price / 100 for price in asks],
        list(asks.values()),
        height=0.008,
        color="red",
        label="Asks",
    )

    ax.set_xlabel("Shares available")
    ax.set_ylabel("Price ($)")
    ax.set_title("Simulated Order Book")
    ax.legend()

    plt.tight_layout()
    plt.show()