import tkinter as tk
from simulation import run_simulation
from tkinter import ttk

from itertools import accumulate
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from decimal import Decimal, InvalidOperation
from tkinter import messagebox
from order_book import Order

import random

root = tk.Tk()
root.title("Order Book Simulator")
root.geometry("1400x850")
root.configure(bg="#101318")

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=3)
root.columnconfigure(2, weight=1)

panels = {}

for column, name in enumerate(["DEPTH OF MARKET", "CUMULATIVE DEPTH", "ORDER ENTRY"]):
    panel = tk.Frame(root, bg="#181d25")
    panel.grid(
        row=0, 
        column=column, 
        sticky="nsew", 
        padx=6,
        pady=10,)
    
    title = tk.Label(
        panel,
        text=name,
        bg="#181d25",
        fg="#aab2bf",
        font=("Arial", 11, "bold"),
    )
    
    title.pack(anchor="w",padx=12,pady=12)
    
    panels[name] = panel

book = run_simulation(num_steps=1000)

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

ladder.tag_configure("bid", foreground="#36b5a5")
ladder.tag_configure("ask", foreground="#ef6464")
ladder.tag_configure("spread", foreground="#f0c541")

bids = book.get_depth("buy")
asks = book.get_depth("sell")

def refresh_ladder():
    # Clear the old rows.
    for item in ladder.get_children():
        ladder.delete(item)

    bids = book.get_depth("buy")
    asks = book.get_depth("sell")

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

    for price in sorted(bids, reverse=True):
        ladder.insert(
            "",
            "end",
            values=(bids[price], f"{price / 100:.2f}", ""),
            tags=("bid",),
        )
# Create the chart and embed it once.
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

    bid_prices = sorted(bids, reverse=True)
    ask_prices = sorted(asks)

    bid_totals = list(accumulate(bids[p] for p in bid_prices))
    ask_totals = list(accumulate(asks[p] for p in ask_prices))

    bid_x = [p / 100 for p in reversed(bid_prices)]
    bid_y = list(reversed(bid_totals))

    ask_x = [p / 100 for p in ask_prices]
    ask_y = ask_totals

    ax.step(bid_x, bid_y, where="pre", color="#36b5a5")
    ax.fill_between(
        bid_x, bid_y,
        step="pre",
        color="#36b5a5",
        alpha=0.2,
    )

    ax.step(ask_x, ask_y, where="post", color="#ef6464")
    ax.fill_between(
        ask_x, ask_y,
        step="post",
        color="#ef6464",
        alpha=0.2,
    )

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
    canvas.draw_idle()


def refresh_display():
    refresh_ladder()
    refresh_chart()

entry_panel = panels["ORDER ENTRY"]

side_var = tk.StringVar(value="buy")
type_var = tk.StringVar(value="limit")

# Continue after the IDs used by the simulation.
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

        if type_var.get() == "market":
            book.add_market_order(order)
        else:
            book.add_order(order)

    except (ValueError, InvalidOperation) as error:
        messagebox.showerror("Invalid order", str(error))
        return

    next_order_id += 1
    refresh_display()


ttk.Button(
    entry_panel,
    text="Submit Order",
    command=submit_order,
).pack(fill="x", padx=12, pady=16)

rng = random.Random()
running = False


def generate_random_order():
    global next_order_id

    side = rng.choice(["buy", "sell"])
    quantity = rng.randint(1, 20)

    # Place limit orders around the current midpoint.
    if book.bids and book.asks:
        reference = (book.bids[0].price + book.asks[0].price) // 2
    elif book.bids:
        reference = book.bids[0].price
    elif book.asks:
        reference = book.asks[0].price
    else:
        reference = 10000

    price = max(1, reference + rng.randint(-30, 30))

    order = Order(next_order_id, side, price, quantity)
    book.add_order(order)
    next_order_id += 1


def simulation_tick():
    if not running:
        return

    generate_random_order()
    refresh_display()

    # Schedule the next order in 500 milliseconds.
    root.after(500, simulation_tick)


def toggle_simulation():
    global running

    running = not running

    if running:
        flow_button.configure(text="Pause Flow")
        simulation_tick()
    else:
        flow_button.configure(text="Start Flow")


flow_button = ttk.Button(
    entry_panel,
    text="Start Flow",
    command=toggle_simulation,
)
flow_button.pack(fill="x", padx=12, pady=10)

refresh_display()
root.mainloop()