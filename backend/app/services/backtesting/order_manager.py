"""
Order management for backtesting engine.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pandas as pd

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class TimeInForce(Enum):
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill

@dataclass
class Order:
    """Order representation"""
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    timestamp: datetime
    
    # Optional parameters
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Execution tracking
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    remaining_quantity: float = field(init=False)
    
    # Timestamps
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Costs
    commission: float = 0.0
    slippage: float = 0.0
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    notes: str = ""
    
    def __post_init__(self):
        self.remaining_quantity = self.quantity
        if self.submitted_at is None:
            self.submitted_at = self.timestamp
    
    @property
    def is_complete(self) -> bool:
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIAL]
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage"""
        return (self.filled_quantity / self.quantity) * 100 if self.quantity > 0 else 0

@dataclass
class Fill:
    """Order fill representation"""
    order_id: str
    symbol: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0
    fill_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    venue: str = "BACKTEST"
    notes: str = ""

class OrderManager:
    """Manages orders during backtesting"""
    
    def __init__(self, commission_rate: float = 0.001, slippage_rate: float = 0.0005):
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        # Order tracking
        self.pending_orders: Dict[str, Order] = {}
        self.filled_orders: Dict[str, Order] = {}
        self.cancelled_orders: Dict[str, Order] = {}
        self.all_orders: Dict[str, Order] = {}
        
        # Fill tracking
        self.fills: List[Fill] = []
        
        # Statistics
        self.total_orders = 0
        self.total_fills = 0
        self.total_commission = 0.0
        self.total_slippage = 0.0
        
        logger.info(f"Initialized OrderManager with {commission_rate:.4f} commission, {slippage_rate:.4f} slippage")
    
    def submit_order(self, order: Order) -> str:
        """Submit an order for execution"""
        try:
            # Validate order
            if not self._validate_order(order):
                order.status = OrderStatus.REJECTED
                order.notes = "Order validation failed"
                logger.warning(f"Order rejected: {order.order_id} - validation failed")
                return order.order_id
            
            # Add to tracking
            self.pending_orders[order.order_id] = order
            self.all_orders[order.order_id] = order
            self.total_orders += 1
            
            order.status = OrderStatus.PENDING
            order.submitted_at = datetime.now()
            
            logger.debug(f"Order submitted: {order.side.value} {order.quantity} {order.symbol} @ {order.order_type.value}")
            
            return order.order_id
            
        except Exception as e:
            logger.error(f"Error submitting order: {str(e)}")
            order.status = OrderStatus.REJECTED
            order.notes = f"Submission error: {str(e)}"
            return order.order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        try:
            if order_id not in self.pending_orders:
                logger.warning(f"Cannot cancel order {order_id}: not found in pending orders")
                return False
            
            order = self.pending_orders[order_id]
            
            # Move to cancelled
            del self.pending_orders[order_id]
            self.cancelled_orders[order_id] = order
            
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.now()
            
            logger.debug(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False
    
    def process_market_orders(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> List[Fill]:
        """Process all pending market orders"""
        fills = []
        orders_to_remove = []
        
        for order_id, order in self.pending_orders.items():
            if order.order_type == OrderType.MARKET:
                try:
                    # Get current price
                    current_price = self._get_current_price(order.symbol, current_date, market_data)
                    if current_price is None:
                        continue
                    
                    # Execute market order
                    fill = self._execute_order(order, current_price, current_date)
                    if fill:
                        fills.append(fill)
                    
                    # Mark for removal if fully filled
                    if order.is_complete:
                        orders_to_remove.append(order_id)
                        
                except Exception as e:
                    logger.error(f"Error processing market order {order_id}: {str(e)}")
                    continue
        
        # Remove completed orders
        for order_id in orders_to_remove:
            self._complete_order(order_id)
        
        return fills
    
    def process_limit_orders(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> List[Fill]:
        """Process pending limit orders"""
        fills = []
        orders_to_remove = []
        
        for order_id, order in self.pending_orders.items():
            if order.order_type == OrderType.LIMIT:
                try:
                    # Check if limit price is reached
                    if self._is_limit_order_triggered(order, current_date, market_data):
                        fill = self._execute_order(order, order.limit_price, current_date)
                        if fill:
                            fills.append(fill)
                        
                        if order.is_complete:
                            orders_to_remove.append(order_id)
                            
                except Exception as e:
                    logger.error(f"Error processing limit order {order_id}: {str(e)}")
                    continue
        
        # Remove completed orders
        for order_id in orders_to_remove:
            self._complete_order(order_id)
        
        return fills
    
    def process_stop_orders(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> List[Fill]:
        """Process pending stop orders"""
        fills = []
        orders_to_remove = []
        
        for order_id, order in self.pending_orders.items():
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                try:
                    # Check if stop price is reached
                    if self._is_stop_order_triggered(order, current_date, market_data):
                        if order.order_type == OrderType.STOP:
                            # Convert to market order
                            current_price = self._get_current_price(order.symbol, current_date, market_data)
                            if current_price:
                                fill = self._execute_order(order, current_price, current_date)
                                if fill:
                                    fills.append(fill)
                        else:  # STOP_LIMIT
                            # Convert to limit order (will be processed in next cycle)
                            order.order_type = OrderType.LIMIT
                            continue
                        
                        if order.is_complete:
                            orders_to_remove.append(order_id)
                            
                except Exception as e:
                    logger.error(f"Error processing stop order {order_id}: {str(e)}")
                    continue
        
        # Remove completed orders
        for order_id in orders_to_remove:
            self._complete_order(order_id)
        
        return fills
    
    def expire_day_orders(self, current_date: datetime):
        """Expire DAY orders at end of trading day"""
        expired_orders = []
        
        for order_id, order in self.pending_orders.items():
            if order.time_in_force == TimeInForce.DAY:
                # Check if order is from previous day
                if order.submitted_at and order.submitted_at.date() < current_date.date():
                    expired_orders.append(order_id)
        
        # Cancel expired orders
        for order_id in expired_orders:
            self.cancel_order(order_id)
    
    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters"""
        try:
            # Basic validation
            if order.quantity <= 0:
                return False
            
            if not order.symbol:
                return False
            
            # Type-specific validation
            if order.order_type == OrderType.LIMIT and order.limit_price is None:
                return False
            
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order.stop_price is None:
                return False
            
            if order.order_type == OrderType.STOP_LIMIT and order.limit_price is None:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _get_current_price(self, symbol: str, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> Optional[float]:
        """Get current price for symbol"""
        try:
            if symbol not in market_data:
                return None
            
            data = market_data[symbol]
            
            # Find closest available date
            available_dates = data.index[data.index <= current_date]
            if len(available_dates) == 0:
                return None
            
            latest_date = available_dates[-1]
            return data.loc[latest_date, 'close']
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None
    
    def _is_limit_order_triggered(self, order: Order, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> bool:
        """Check if limit order should be triggered"""
        try:
            if symbol not in market_data:
                return False
            
            data = market_data[order.symbol]
            available_dates = data.index[data.index <= current_date]
            if len(available_dates) == 0:
                return False
            
            latest_date = available_dates[-1]
            current_data = data.loc[latest_date]
            
            if order.side == OrderSide.BUY:
                # Buy limit: trigger if market price <= limit price
                return current_data['low'] <= order.limit_price
            else:
                # Sell limit: trigger if market price >= limit price
                return current_data['high'] >= order.limit_price
                
        except Exception:
            return False
    
    def _is_stop_order_triggered(self, order: Order, current_date: datetime, market_data: Dict[str, pd.DataFrame]) -> bool:
        """Check if stop order should be triggered"""
        try:
            if order.symbol not in market_data:
                return False
            
            data = market_data[order.symbol]
            available_dates = data.index[data.index <= current_date]
            if len(available_dates) == 0:
                return False
            
            latest_date = available_dates[-1]
            current_data = data.loc[latest_date]
            
            if order.side == OrderSide.BUY:
                # Buy stop: trigger if market price >= stop price
                return current_data['high'] >= order.stop_price
            else:
                # Sell stop: trigger if market price <= stop price
                return current_data['low'] <= order.stop_price
                
        except Exception:
            return False
    
    def _execute_order(self, order: Order, execution_price: float, execution_time: datetime) -> Optional[Fill]:
        """Execute an order at given price"""
        try:
            # Calculate slippage
            slippage_amount = execution_price * self.slippage_rate
            if order.side == OrderSide.BUY:
                actual_price = execution_price + slippage_amount
            else:
                actual_price = execution_price - slippage_amount
            
            # Ensure positive price
            actual_price = max(actual_price, 0.01)
            
            # Calculate commission
            trade_value = order.remaining_quantity * actual_price
            commission = trade_value * self.commission_rate
            
            # Create fill
            fill = Fill(
                order_id=order.order_id,
                symbol=order.symbol,
                quantity=order.remaining_quantity,
                price=actual_price,
                timestamp=execution_time,
                commission=commission,
                slippage=slippage_amount * order.remaining_quantity
            )
            
            # Update order
            order.filled_quantity += fill.quantity
            order.remaining_quantity = max(0, order.quantity - order.filled_quantity)
            order.commission += commission
            order.slippage += fill.slippage
            
            # Update average fill price
            total_value = (order.avg_fill_price * (order.filled_quantity - fill.quantity)) + (actual_price * fill.quantity)
            order.avg_fill_price = total_value / order.filled_quantity if order.filled_quantity > 0 else actual_price
            
            if order.is_complete:
                order.status = OrderStatus.FILLED
                order.filled_at = execution_time
            else:
                order.status = OrderStatus.PARTIAL
            
            # Track fills
            self.fills.append(fill)
            self.total_fills += 1
            self.total_commission += commission
            self.total_slippage += fill.slippage
            
            logger.debug(f"Order filled: {fill.quantity} {fill.symbol} @ {actual_price:.2f}")
            
            return fill
            
        except Exception as e:
            logger.error(f"Error executing order {order.order_id}: {str(e)}")
            return None
    
    def _complete_order(self, order_id: str):
        """Move order from pending to filled"""
        if order_id in self.pending_orders:
            order = self.pending_orders[order_id]
            del self.pending_orders[order_id]
            self.filled_orders[order_id] = order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.all_orders.get(order_id)
    
    def get_pending_orders(self, symbol: str = None) -> List[Order]:
        """Get pending orders, optionally filtered by symbol"""
        orders = list(self.pending_orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_filled_orders(self, symbol: str = None) -> List[Order]:
        """Get filled orders, optionally filtered by symbol"""
        orders = list(self.filled_orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_fills(self, symbol: str = None, start_date: datetime = None, end_date: datetime = None) -> List[Fill]:
        """Get fills with optional filters"""
        fills = self.fills
        
        if symbol:
            fills = [f for f in fills if f.symbol == symbol]
        
        if start_date:
            fills = [f for f in fills if f.timestamp >= start_date]
        
        if end_date:
            fills = [f for f in fills if f.timestamp <= end_date]
        
        return fills
    
    def get_order_statistics(self) -> Dict:
        """Get order execution statistics"""
        return {
            'total_orders': self.total_orders,
            'pending_orders': len(self.pending_orders),
            'filled_orders': len(self.filled_orders),
            'cancelled_orders': len(self.cancelled_orders),
            'total_fills': self.total_fills,
            'total_commission': self.total_commission,
            'total_slippage': self.total_slippage,
            'avg_commission_per_trade': self.total_commission / self.total_fills if self.total_fills > 0 else 0,
            'avg_slippage_per_trade': self.total_slippage / self.total_fills if self.total_fills > 0 else 0
        }
    
    def reset(self):
        """Reset order manager state"""
        self.pending_orders.clear()
        self.filled_orders.clear()
        self.cancelled_orders.clear()
        self.all_orders.clear()
        self.fills.clear()
        
        self.total_orders = 0
        self.total_fills = 0
        self.total_commission = 0.0
        self.total_slippage = 0.0
        
        logger.info("OrderManager reset to initial state")