import matplotlib.pyplot as plt

from simulation import run_simulation

def plot_order_book(book):
    bids = book.get_depth("buy")
    asks = book.get_depth("sell")
    
    fig, ax = plt.subplots()
    
    ax.barh([price/100 for price in bids],list(bids.values()), height=.008, color="green",label="Bids",)
    
    ax.barh([price/100 for price in asks], list(asks.values()), height=.008, color="red", label="Asks",)
    
    ax.set_xlabel("Shares available")
    ax.set_ylabel("Price($)")
    ax.set_title("Simulated Order Book")
    ax.legend()
    
    plt.tight_layout()
    plt.show()
    
if __name__ == "__main__":
    book = run_simulation(num_steps=1000)
    plot_order_book(book)