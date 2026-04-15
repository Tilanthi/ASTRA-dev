# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Market Simulation Engine

Agent-based market simulation with realistic order book dynamics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import deque
from enum import Enum


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """An order in the market."""
    id: str
    type: OrderType
    price: float
    quantity: float
    timestamp: int
    trader_id: str


class OrderBook:
    """
    Limit order book for price discovery.

    Maintains bids (buy orders) and asks (sell orders)
    and matches them when prices cross.
    """

    def __init__(self, tick_size: float = 0.01):
        self.tick_size = tick_size

        self.bids: List[Order] = []  # Buy orders (sorted descending)
        self.asks: List[Order] = []  # Sell orders (sorted ascending)

        self.trades: List[Dict] = []
        self.last_price: Optional[float] = None

    def add_order(self, order: Order) -> List[Dict]:
        """
        Add order to book and match if possible.

        Args:
            order: Order to add

        Returns:
            List of executed trades
        """
        trades = []

        if order.type == OrderType.BUY:
            # Buy order - check if can match with asks
            while self.asks and order.quantity > 0:
                best_ask = self.asks[0]

                if order.price >= best_ask.price:
                    # Match!
                    trade_price = best_ask.price
                    trade_quantity = min(order.quantity, best_ask.quantity)

                    trade = {
                        'price': trade_price,
                        'quantity': trade_quantity,
                        'bid_order_id': order.id,
                        'ask_order_id': best_ask.id,
                        'timestamp': order.timestamp
                    }
                    trades.append(trade)
                    self.trades.append(trade)

                    # Update quantities
                    order.quantity -= trade_quantity
                    best_ask.quantity -= trade_quantity

                    # Remove filled ask
                    if best_ask.quantity <= 0:
                        self.asks.pop(0)
                else:
                    break

            # Add remaining bid to book
            if order.quantity > 0:
                self._insert_bid(order)

        else:  # SELL order
            # Sell order - check if can match with bids
            while self.bids and order.quantity > 0:
                best_bid = self.bids[0]

                if order.price <= best_bid.price:
                    # Match!
                    trade_price = best_bid.price
                    trade_quantity = min(order.quantity, best_bid.quantity)

                    trade = {
                        'price': trade_price,
                        'quantity': trade_quantity,
                        'bid_order_id': best_bid.id,
                        'ask_order_id': order.id,
                        'timestamp': order.timestamp
                    }
                    trades.append(trade)
                    self.trades.append(trade)

                    # Update quantities
                    order.quantity -= trade_quantity
                    best_bid.quantity -= trade_quantity

                    # Remove filled bid
                    if best_bid.quantity <= 0:
                        self.bids.pop(0)
                else:
                    break

            # Add remaining ask to book
            if order.quantity > 0:
                self._insert_ask(order)

        # Update last price
        if trades:
            self.last_price = trades[-1]['price']

        return trades

    def _insert_bid(self, order: Order) -> None:
        """Insert bid order maintaining sorted order."""
        # Find position (descending price)
        for i, bid in enumerate(self.bids):
            if order.price > bid.price:
                self.bids.insert(i, order)
                return
        self.bids.append(order)

    def _insert_ask(self, order: Order) -> None:
        """Insert ask order maintaining sorted order."""
        # Find position (ascending price)
        for i, ask in enumerate(self.asks):
            if order.price < ask.price:
                self.asks.insert(i, order)
                return
        self.asks.append(order)

    def get_mid_price(self) -> Optional[float]:
        """Get mid price (average of best bid and ask)."""
        if not self.bids or not self.asks:
            return self.last_price

        return (self.bids[0].price + self.asks[0].price) / 2

    def get_spread(self) -> Optional[float]:
        """Get bid-ask spread."""
        if not self.bids or not self.asks:
            return None

        return self.asks[0].price - self.bids[0].price

    def get_depth(self, levels: int = 5) -> Dict[str, List[Tuple[float, float]]]:
        """Get order book depth."""
        bids = [(o.price, o.quantity) for o in self.bids[:levels]]
        asks = [(o.price, o.quantity) for o in self.asks[:levels]]

        return {'bids': bids, 'asks': asks}


@dataclass
class TraderAgent:
    """A trading agent."""
    id: str
    strategy: str
    params: Dict[str, Any]


class MarketSimulation:
    """
    Agent-based market simulation.

    Simulates multiple traders interacting through an order book.
    """

    def __init__(self,
                 n_agents: int = 100,
                 tick_size: float = 0.01):
        self.n_agents = n_agents
        self.order_book = OrderBook(tick_size)
        self.agents: List[TraderAgent] = []
        self.time = 0

        self.price_history: List[float] = []
        self.volume_history: List[float] = []

    def add_agent(self, agent: TraderAgent) -> None:
        """Add trading agent."""
        self.agents.append(agent)

    def create_default_agents(self) -> None:
        """Create default set of trading agents."""
        # Market makers (provide liquidity)
        for i in range(10):
            agent = TraderAgent(
                id=f"mm_{i}",
                strategy="market_maker",
                params={'spread_bps': 10, 'qty_mean': 100, 'qty_std': 20}
            )
            self.add_agent(agent)

        # Noise traders (random trading)
        for i in range(50):
            agent = TraderAgent(
                id=f"noise_{i}",
                strategy="noise",
                params={'buy_prob': 0.5, 'qty_mean': 50}
            )
            self.add_agent(agent)

        # Momentum traders
        for i in range(20):
            agent = TraderAgent(
                id=f"mom_{i}",
                strategy="momentum",
                params={'lookback': 10, 'threshold': 0.02}
            )
            self.add_agent(agent)

        # Mean reversion traders
        for i in range(20):
            agent = TraderAgent(
                id=f"mr_{i}",
                strategy="mean_reversion",
                params={'lookback': 20, 'threshold': 0.03}
            )
            self.add_agent(agent)

    def step(self) -> Dict[str, Any]:
        """
        Advance simulation by one step.

        Returns:
            Market state
        """
        self.time += 1

        # Each agent decides whether to trade
        for agent in self.agents:
            if np.random.random() < 0.1:  # 10% chance to trade each step
                orders = self._generate_orders(agent)
                for order in orders:
                    self.order_book.add_order(order)

        # Record market state
        mid_price = self.order_book.get_mid_price()
        if mid_price:
            self.price_history.append(mid_price)

        # Compute volume
        recent_trades = [t for t in self.order_book.trades
                        if t['timestamp'] == self.time]
        volume = sum(t['quantity'] for t in recent_trades)
        self.volume_history.append(volume)

        return {
            'time': self.time,
            'mid_price': mid_price,
            'spread': self.order_book.get_spread(),
            'volume': volume
        }

    def _generate_orders(self, agent: TraderAgent) -> List[Order]:
        """Generate orders from agent."""
        orders = []

        if agent.strategy == "market_maker":
            # Place both bid and ask around mid price
            mid = self.order_book.get_mid_price()
            if mid:
                spread = mid * agent.params['spread_bps'] / 10000

                # Buy order (bid)
                bid_order = Order(
                    id=f"{agent.id}_bid_{self.time}",
                    type=OrderType.BUY,
                    price=mid - spread/2,
                    quantity=max(1, int(np.random.normal(
                        agent.params['qty_mean'],
                        agent.params['qty_std']
                    ))),
                    timestamp=self.time,
                    trader_id=agent.id
                )
                orders.append(bid_order)

                # Sell order (ask)
                ask_order = Order(
                    id=f"{agent.id}_ask_{self.time}",
                    type=OrderType.SELL,
                    price=mid + spread/2,
                    quantity=max(1, int(np.random.normal(
                        agent.params['qty_mean'],
                        agent.params['qty_std']
                    ))),
                    timestamp=self.time,
                    trader_id=agent.id
                )
                orders.append(ask_order)

        elif agent.strategy == "noise":
            # Random buy or sell
            mid = self.order_book.get_mid_price() or 100.0

            if np.random.random() < agent.params['buy_prob']:
                order_type = OrderType.BUY
            else:
                order_type = OrderType.SELL

            order = Order(
                id=f"{agent.id}_{self.time}",
                type=order_type,
                price=mid,
                quantity=int(np.random.poisson(agent.params['qty_mean'])),
                timestamp=self.time,
                trader_id=agent.id
            )
            orders.append(order)

        elif agent.strategy == "momentum":
            # Buy if price went up, sell if down
            if len(self.price_history) >= agent.params['lookback'] + 1:
                recent_returns = [
                    (self.price_history[-i] - self.price_history[-i-1]) /
                    max(self.price_history[-i-1], 0.01)  # Avoid division by zero
                    for i in range(1, min(agent.params['lookback']+1, len(self.price_history)))
                ]
                avg_return = np.mean(recent_returns)

                mid = self.order_book.get_mid_price() or 100.0

                if avg_return > agent.params['threshold']:
                    order = Order(
                        id=f"{agent.id}_{self.time}",
                        type=OrderType.BUY,
                        price=mid,
                        quantity=50,
                        timestamp=self.time,
                        trader_id=agent.id
                    )
                    orders.append(order)
                elif avg_return < -agent.params['threshold']:
                    order = Order(
                        id=f"{agent.id}_{self.time}",
                        type=OrderType.SELL,
                        price=mid,
                        quantity=50,
                        timestamp=self.time,
                        trader_id=agent.id
                    )
                    orders.append(order)

        elif agent.strategy == "mean_reversion":
            # Buy if price low, sell if high (relative to recent mean)
            if len(self.price_history) >= agent.params['lookback']:
                lookback = min(agent.params['lookback'], len(self.price_history))
                recent_prices = self.price_history[-lookback:]
                mean_price = np.mean(recent_prices) if recent_prices else 100.0
                current_price = self.price_history[-1] if self.price_history else 100.0

                deviation = (current_price - mean_price) / max(mean_price, 0.01)

                if deviation > agent.params['threshold']:
                    # Price high - sell
                    order = Order(
                        id=f"{agent.id}_{self.time}",
                        type=OrderType.SELL,
                        price=current_price,
                        quantity=50,
                        timestamp=self.time,
                        trader_id=agent.id
                    )
                    orders.append(order)
                elif deviation < -agent.params['threshold']:
                    # Price low - buy
                    order = Order(
                        id=f"{agent.id}_{self.time}",
                        type=OrderType.BUY,
                        price=current_price,
                        quantity=50,
                        timestamp=self.time,
                        trader_id=agent.id
                    )
                    orders.append(order)

        return orders

    def run(self, steps: int = 1000) -> Dict[str, Any]:
        """
        Run simulation for multiple steps.

        Args:
            steps: Number of steps to simulate

        Returns:
            Simulation results
        """
        for _ in range(steps):
            self.step()

        return {
            'prices': self.price_history,
            'volumes': self.volume_history,
            'total_trades': len(self.order_book.trades),
            'final_price': self.price_history[-1] if self.price_history else None,
            'price_volatility': np.std(self.price_history) if len(self.price_history) > 1 else 0
        }
