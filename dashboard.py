import random
import tkinter as tk
from decimal import Decimal, InvalidOperation
from itertools import accumulate
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from order_book import Order
from simulation import run_simulation


# Window Layout
root = tk.Tk()
root.title("Order Book Simulator")
root.geometry("1400x850")
root.configure(bg="#101318")

# Allow all panels to expand, giving the chart more horizontal space.
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=3)
root.columnconfigure(2, weight=1)

panels = {}

for column, name in enumerate(
    ["DEPTH OF MARKET", "CUMULATIVE DEPTH", "ORDER ENTRY"]
):
    panel = tk.Frame(root, bg="#181d25")
    panel.grid(
        row=0,
        column=column,
        sticky="nsew",
        padx=6,
        pady=10,
    )

    title = tk.Label(
        panel,
        text=name,
        bg="#181d25",
        fg="#aab2bf",
        font=("Arial", 11, "bold"),
    )
    title.pack(anchor="w", padx=12, pady=12)
    panels[name] = panel

# Generate the initial book before starting interactive order flow.
book = run_simulation(num_steps=1000)


# Price Ladder
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#181d25",
    fieldbackground="#181d25",
    foreground="white",
    rowheight=26,
)

style.configure(
    "Treeview.Heading",
    background="#252b35",
    foreground="#aab2bf",
)

ladder = ttk.Treeview(
    panels["DEPTH OF MARKET"],
    columns=("bid", "price", "ask"),
    show="headings",
    selectmode="none",
)

for column, heading in [
    ("bid", "Bid Size"),
    ("price", "Price"),
    ("ask", "Ask Size"),
]:
    ladder.heading(column, text=heading)
    ladder.column(column, width=90, anchor="center")

ladder.pack(fill="both", expand=True, padx=12, pady=12)

# Tags apply different colors to bid, ask, and spread rows.
ladder.tag_configure("bid", foreground="#36b5a5")
ladder.tag_configure("ask", foreground="#ef6464")
ladder.tag_configure("spread", foreground="#f0c541")


def refresh_ladder():
    # Replace displayed rows without changing the actual orders.
    for item in ladder.get_children():
        ladder.delete(item)

    bids = book.get_depth("buy")
    asks = book.get_depth("sell")

    # Descending asks put the best ask directly above the spread.
    for price in sorted(asks, reverse=True):
        ladder.insert(
            "",
            "end",
            values=("", f"{price / 100:.2f}", asks[price]),
            tags=("ask",),
        )

    if bids and asks:
        spread = min(asks) - max(bids)
        ladder.insert(
            "",
            "end",
            values=("", f"— {spread / 100:.2f} —", ""),
            tags=("spread",),
        )

    # The highest bid appears directly below the spread.
    for price in sorted(bids, reverse=True):
        ladder.insert(
            "",
            "end",
            values=(bids[price], f"{price / 100:.2f}", ""),
            tags=("bid",),
        )


# Cumulative Depth Chart
# Create and embed the canvas once; refresh only its plotted contents.
fig = Figure(figsize=(7, 5), facecolor="#181d25")
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(
    fig,
    master=panels["CUMULATIVE DEPTH"],
)
canvas.get_tk_widget().pack(
    fill="both",
    expand=True,
    padx=12,
    pady=12,
)


def refresh_chart():
    ax.clear()
    ax.set_facecolor("#181d25")

    bids = book.get_depth("buy")
    asks = book.get_depth("sell")

    # Accumulate quantities outward from the best price on each side.
    bid_prices = sorted(bids, reverse=True)
    ask_prices = sorted(asks)

    bid_totals = list(accumulate(bids[p] for p in bid_prices))
    ask_totals = list(accumulate(asks[p] for p in ask_prices))

    # Reverse bid coordinates so prices increase from left to right.
    bid_x = [p / 100 for p in reversed(bid_prices)]
    bid_y = list(reversed(bid_totals))

    ask_x = [p / 100 for p in ask_prices]
    ask_y = ask_totals

    ax.step(bid_x, bid_y, where="pre", color="#36b5a5")
    ax.fill_between(
        bid_x,
        bid_y,
        step="pre",
        color="#36b5a5",
        alpha=0.2,
    )

    ax.step(ask_x, ask_y, where="post", color="#ef6464")
    ax.fill_between(
        ask_x,
        ask_y,
        step="post",
        color="#ef6464",
        alpha=0.2,
    )

    # Convert the average best bid/ask from cents to dollars.
    if bids and asks:
        midpoint = (max(bids) + min(asks)) / 200
        ax.axvline(midpoint, color="#f0c541", linestyle="--")

    ax.set_xlabel("Price ($)", color="#aab2bf")
    ax.set_ylabel("Cumulative shares", color="#aab2bf")
    ax.tick_params(colors="#aab2bf")
    ax.grid(alpha=0.15)
    ax.set_ylim(bottom=0)

    for spine in ax.spines.values():
        spine.set_color("#39414d")

    fig.tight_layout()
    # Request a redraw through Tkinter's event loop.
    canvas.draw_idle()


def refresh_display():
    refresh_ladder()
    refresh_chart()


# Manual Order Entry
entry_panel = panels["ORDER ENTRY"]
side_var = tk.StringVar(value="buy")
type_var = tk.StringVar(value="limit")

# Manual and simulated orders share one sequence of unique IDs.
next_order_id = max(book.used_order_ids, default=0) + 1


def add_label(text):
    tk.Label(
        entry_panel,
        text=text,
        bg="#181d25",
        fg="#aab2bf",
    ).pack(anchor="w", padx=12, pady=(10, 4))


add_label("Side")
ttk.Combobox(
    entry_panel,
    textvariable=side_var,
    values=("buy", "sell"),
    state="readonly",
).pack(fill="x", padx=12)

add_label("Order type")
ttk.Combobox(
    entry_panel,
    textvariable=type_var,
    values=("limit", "market"),
    state="readonly",
).pack(fill="x", padx=12)

add_label("Limit price ($)—ignored for market orders")
price_entry = ttk.Entry(entry_panel)
price_entry.insert(0, "100.00")
price_entry.pack(fill="x", padx=12)

add_label("Quantity")
quantity_entry = ttk.Entry(entry_panel)
quantity_entry.insert(0, "10")
quantity_entry.pack(fill="x", padx=12)


def submit_order():
    global next_order_id

    try:
        quantity = int(quantity_entry.get())
        price = None

        if type_var.get() == "limit":
            # Decimal converts dollar input to cents without float rounding.
            cents = Decimal(price_entry.get()) * 100

            if not cents.is_finite():
                raise ValueError("Enter a finite price")

            if cents != cents.to_integral_value():
                raise ValueError("Price must use whole cents")

            price = int(cents)

        order = Order(
            next_order_id,
            side_var.get(),
            price,
            quantity,
        )

        # The matching engine validates and processes the submitted order.
        if type_var.get() == "market":
            book.add_market_order(order)
        else:
            book.add_order(order)

    except (ValueError, InvalidOperation) as error:
        messagebox.showerror("Invalid order", str(error))
        return

    # Advance the ID only after the order is accepted.
    next_order_id += 1
    refresh_display()


ttk.Button(
    entry_panel,
    text="Submit Order",
    command=submit_order,
).pack(fill="x", padx=12, pady=16)


# Live Random Order Flow
rng = random.Random()
running = False


def generate_random_order():
    global next_order_id

    side = rng.choice(["buy", "sell"])
    quantity = rng.randint(1, 20)

    # Use the midpoint, an available quote, or $100 as the reference.
    if book.bids and book.asks:
        reference = (book.bids[0].price + book.asks[0].price) // 2
    elif book.bids:
        reference = book.bids[0].price
    elif book.asks:
        reference = book.asks[0].price
    else:
        reference = 10000

    # Choose a price within 30 cents, keeping it strictly positive.
    price = max(1, reference + rng.randint(-30, 30))

    order = Order(next_order_id, side, price, quantity)
    book.add_order(order)
    next_order_id += 1


def simulation_tick():
    if not running:
        return

    generate_random_order()
    refresh_display()

    # Schedule another step without blocking UI interactions.
    root.after(500, simulation_tick)


def toggle_simulation():
    global running

    running = not running

    if running:
        flow_button.configure(text="Pause Flow")
        simulation_tick()
    else:
        # A pending tick will exit if flow remains paused.
        flow_button.configure(text="Start Flow")


flow_button = ttk.Button(
    entry_panel,
    text="Start Flow",
    command=toggle_simulation,
)
flow_button.pack(fill="x", padx=12, pady=10)


# Render the initial book, then handle window events and callbacks.
refresh_display()
root.mainloop()