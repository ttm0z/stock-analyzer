"""
Portfolio manager for tracking positions, cash, and portfolio value during backtesting.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Individual position in the portfolio"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return abs(self.quantity) * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis of position"""
        return abs(self.quantity) * self.avg_cost
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L"""
        if self.quantity > 0:  # Long position
            return (self.current_price - self.avg_cost) * self.quantity
        else:  # Short position
            return (self.avg_cost - self.current_price) * abs(self.quantity)
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage"""
        if self.cost_basis > 0:
            return (self.unrealized_pnl / self.cost_basis) * 100
        return 0.0
    
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0

@dataclass
class Transaction:
    """Portfolio transaction record"""
    symbol: str
    transaction_type: str  # BUY, SELL, DIVIDEND, etc.
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    cash_impact: float  # Net cash flow (negative for purchases)
    order_id: str = ""
    notes: str = ""

class PortfolioManager:
    """Manages portfolio state during backtesting"""
    
    def __init__(self, initial_capital: float, currency: str = 'USD'):
        self.initial_capital = initial_capital
        self.currency = currency
        
        # Portfolio state
        self.cash_balance = initial_capital
        self.positions: Dict[str, Position] = {}
        self.transactions: List[Transaction] = []
        
        # Performance tracking
        self.total_commission_paid = 0.0
        self.total_slippage_cost = 0.0
        self.realized_pnl = 0.0
        
        # Portfolio history
        self.value_history: List[Tuple[datetime, float]] = []
        self.position_history: List[Tuple[datetime, Dict[str, float]]] = []
        
        logger.info(f"Initialized portfolio with {initial_capital:,.2f} {currency}")
    
    def execute_trade(self, symbol: str, quantity: float, price: float, 
                     commission: float, timestamp: datetime, order_id: str = "") -> bool:
        """
        Execute a trade and update portfolio
        
        Args:
            symbol: Trading symbol
            quantity: Quantity (positive for buy, negative for sell)
            price: Execution price
            commission: Commission cost
            timestamp: Execution timestamp
            order_id: Order identifier
        
        Returns:
            True if trade executed successfully
        """
        try:
            # Calculate trade value and cash impact
            trade_value = abs(quantity) * price
            cash_impact = -quantity * price - commission  # Negative for purchases
            
            # Check if we have enough cash for purchases
            if quantity > 0 and cash_impact < -self.cash_balance:
                logger.warning(f"Insufficient cash for {symbol} purchase: need {-cash_impact:.2f}, have {self.cash_balance:.2f}")
                return False
            
            # Check if we have enough shares for sales
            if quantity < 0:
                current_position = self.positions.get(symbol)
                if not current_position or current_position.quantity < abs(quantity):
                    logger.warning(f"Insufficient shares for {symbol} sale: trying to sell {abs(quantity)}, have {current_position.quantity if current_position else 0}")
                    return False
            
            # Update cash balance
            self.cash_balance += cash_impact
            self.total_commission_paid += commission
            
            # Update position
            self._update_position(symbol, quantity, price, timestamp)
            
            # Record transaction
            transaction = Transaction(
                symbol=symbol,
                transaction_type="BUY" if quantity > 0 else "SELL",
                quantity=quantity,
                price=price,
                commission=commission,
                timestamp=timestamp,
                cash_impact=cash_impact,
                order_id=order_id
            )
            self.transactions.append(transaction)
            
            logger.debug(f"Executed trade: {transaction.transaction_type} {abs(quantity)} {symbol} @ {price:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {str(e)}")
            return False
    
    def _update_position(self, symbol: str, quantity: float, price: float, timestamp: datetime):
        """Update position with new trade"""
        current_position = self.positions.get(symbol)
        
        if not current_position:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
                last_updated=timestamp
            )
        else:
            # Existing position
            old_quantity = current_position.quantity
            new_quantity = old_quantity + quantity
            
            if new_quantity == 0:
                # Position closed
                pnl = self._calculate_realized_pnl(current_position, quantity, price)
                self.realized_pnl += pnl
                del self.positions[symbol]
                logger.debug(f"Closed position in {symbol}, realized P&L: {pnl:.2f}")
            
            elif (old_quantity > 0 and new_quantity > 0) or (old_quantity < 0 and new_quantity < 0):
                # Adding to existing position (same direction)
                total_cost = (current_position.avg_cost * abs(old_quantity)) + (price * abs(quantity))
                total_quantity = abs(new_quantity)
                new_avg_cost = total_cost / total_quantity if total_quantity > 0 else price
                
                current_position.quantity = new_quantity
                current_position.avg_cost = new_avg_cost
                current_position.last_updated = timestamp
            
            else:
                # Reducing position or changing direction
                if abs(quantity) < abs(old_quantity):
                    # Partial close
                    pnl = self._calculate_realized_pnl(current_position, quantity, price)
                    self.realized_pnl += pnl
                    
                    current_position.quantity = new_quantity
                    current_position.last_updated = timestamp
                    logger.debug(f"Reduced position in {symbol}, realized P&L: {pnl:.2f}")
                
                else:
                    # Full close and reverse
                    close_quantity = -old_quantity
                    reverse_quantity = quantity - close_quantity
                    
                    # Realize P&L from closing
                    pnl = self._calculate_realized_pnl(current_position, close_quantity, price)
                    self.realized_pnl += pnl
                    
                    # Create new position in opposite direction
                    current_position.quantity = reverse_quantity
                    current_position.avg_cost = price
                    current_position.last_updated = timestamp
                    
                    logger.debug(f"Reversed position in {symbol}, realized P&L: {pnl:.2f}")
    
    def _calculate_realized_pnl(self, position: Position, quantity: float, price: float) -> float:
        """Calculate realized P&L for a position reduction"""
        if position.quantity > 0:  # Long position
            return (price - position.avg_cost) * abs(quantity)
        else:  # Short position
            return (position.avg_cost - price) * abs(quantity)
    
    def update_prices(self, current_prices: Dict[str, float], timestamp: datetime):
        """Update current prices for all positions"""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.last_updated = timestamp
    
    def get_total_value(self) -> float:
        """Get total portfolio value"""
        market_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash_balance + market_value
    
    def get_cash_balance(self) -> float:
        """Get current cash balance"""
        return self.cash_balance
    
    def get_invested_value(self) -> float:
        """Get total invested value (market value of positions)"""
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_positions(self) -> Dict[str, float]:
        """Get current positions as symbol -> quantity dict"""
        return {symbol: pos.quantity for symbol, pos in self.positions.items()}
    
    def get_position_details(self) -> Dict[str, Position]:
        """Get detailed position information"""
        return self.positions.copy()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        return self.positions.get(symbol)
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_realized_pnl(self) -> float:
        """Get total realized P&L"""
        return self.realized_pnl
    
    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.realized_pnl + self.get_unrealized_pnl()
    
    def get_total_return(self) -> float:
        """Get total return percentage"""
        total_value = self.get_total_value()
        return (total_value / self.initial_capital - 1) * 100
    
    def get_portfolio_weights(self) -> Dict[str, float]:
        """Get position weights as percentage of portfolio"""
        total_value = self.get_total_value()
        if total_value <= 0:
            return {}
        
        weights = {}
        for symbol, position in self.positions.items():
            weights[symbol] = (position.market_value / total_value) * 100
        
        return weights
    
    def get_sector_allocation(self, sector_map: Dict[str, str] = None) -> Dict[str, float]:
        """Get allocation by sector"""
        if not sector_map:
            return {}
        
        sector_values = {}
        total_value = self.get_total_value()
        
        for symbol, position in self.positions.items():
            sector = sector_map.get(symbol, 'Unknown')
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += position.market_value
        
        # Convert to percentages
        sector_allocation = {}
        for sector, value in sector_values.items():
            sector_allocation[sector] = (value / total_value) * 100 if total_value > 0 else 0
        
        return sector_allocation
    
    def get_transactions(self, symbol: str = None, 
                        start_date: datetime = None, 
                        end_date: datetime = None) -> List[Transaction]:
        """Get transaction history with optional filters"""
        transactions = self.transactions
        
        if symbol:
            transactions = [t for t in transactions if t.symbol == symbol]
        
        if start_date:
            transactions = [t for t in transactions if t.timestamp >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t.timestamp <= end_date]
        
        return transactions
    
    def get_performance_summary(self) -> Dict:
        """Get portfolio performance summary"""
        total_value = self.get_total_value()
        total_return = self.get_total_return()
        unrealized_pnl = self.get_unrealized_pnl()
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash_balance': self.cash_balance,
            'invested_value': self.get_invested_value(),
            'total_return_pct': total_return,
            'total_return_dollar': total_value - self.initial_capital,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': self.get_total_pnl(),
            'total_commission': self.total_commission_paid,
            'total_slippage': self.total_slippage_cost,
            'num_positions': len(self.positions),
            'num_transactions': len(self.transactions),
            'currency': self.currency
        }
    
    def record_snapshot(self, timestamp: datetime):
        """Record portfolio snapshot for history"""
        total_value = self.get_total_value()
        positions = self.get_positions()
        
        self.value_history.append((timestamp, total_value))
        self.position_history.append((timestamp, positions.copy()))
    
    def get_value_history(self) -> pd.Series:
        """Get portfolio value history as pandas Series"""
        if not self.value_history:
            return pd.Series()
        
        dates, values = zip(*self.value_history)
        return pd.Series(values, index=dates)
    
    def reset(self):
        """Reset portfolio to initial state"""
        self.cash_balance = self.initial_capital
        self.positions.clear()
        self.transactions.clear()
        self.total_commission_paid = 0.0
        self.total_slippage_cost = 0.0
        self.realized_pnl = 0.0
        self.value_history.clear()
        self.position_history.clear()
        
        logger.info("Portfolio reset to initial state")
    
    def validate_portfolio_state(self) -> List[str]:
        """Validate portfolio state and return any issues found"""
        issues = []
        
        # Check for negative cash (with small tolerance for rounding)
        if self.cash_balance < -0.01:
            issues.append(f"Negative cash balance: {self.cash_balance:.2f}")
        
        # Check for zero quantity positions
        for symbol, position in self.positions.items():
            if abs(position.quantity) < 1e-8:
                issues.append(f"Zero quantity position for {symbol}")
            
            if position.current_price <= 0:
                issues.append(f"Invalid price for {symbol}: {position.current_price}")
        
        # Check total value calculation
        calculated_value = self.cash_balance + sum(pos.market_value for pos in self.positions.values())
        reported_value = self.get_total_value()
        if abs(calculated_value - reported_value) > 0.01:
            issues.append(f"Value calculation mismatch: {calculated_value:.2f} vs {reported_value:.2f}")
        
        return issues