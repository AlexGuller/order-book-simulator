# Order Book Simulator

A Python limit order book and matching engine with an interactive desktop dashboard.

## Features

- Limit and market buy/sell orders
- Price-time priority matching
- Partial fills and order cancellation
- Order validation and unique order IDs
- Price ladder showing aggregated bid and ask quantities
- Cumulative depth chart with midpoint marker
- Manual order entry

## Matching Rules

Buy orders match against the lowest available ask. Sell orders match against the highest available bid.

Orders at the same price execute in arrival order. Trades execute at the resting order's price, and partially filled limit orders retain their remaining quantity.

Unfilled market-order quantities do not enter the book. Prices are stored as integer cents to avoid floating-point rounding errors.

## Setup

Requires Python with Tkinter support.
