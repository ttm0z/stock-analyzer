"""
Execution engine for processing orders and updating portfolio state.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from .portfolio_manager import PortfolioManager
from .order_manager import OrderManager, Order, Fill, OrderType, OrderSide

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Handles order execution and portfolio updates"""
    
    def __init__(self, portfolio_manager: PortfolioManager, order_manager: OrderManager,
                 execution_delay: int = 0, market_impact: bool = True):
        self.portfolio_manager = portfolio_manager
        self.order_manager = order_manager
        self.execution_delay = execution_delay  # Days delay for order execution
        self.market_impact = market_impact
        
        # Execution tracking
        self.executed_trades = []
        self.execution_errors = []
        
        logger.info(f"Initialized ExecutionEngine with {execution_delay} day delay, market_impact={market_impact}")
    
    def execute_orders(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]):
        """Execute all eligible orders for current date"""
        try:
            # Expire day orders first
            self.order_manager.expire_day_orders(current_date)
            
            # Process different order types in sequence
            fills = []
            
            # 1. Process market orders (highest priority)
            market_fills = self.order_manager.process_market_orders(current_date, market_data)
            fills.extend(market_fills)
            
            # 2. Process stop orders (convert to market/limit)
            stop_fills = self.order_manager.process_stop_orders(current_date, market_data)
            fills.extend(stop_fills)
            
            # 3. Process limit orders
            limit_fills = self.order_manager.process_limit_orders(current_date, market_data)
            fills.extend(limit_fills)
            
            # Execute fills in portfolio
            for fill in fills:
                self._execute_fill_in_portfolio(fill, current_date)
            
            if fills:
                logger.debug(f"Executed {len(fills)} fills on {current_date.date()}")
            
        except Exception as e:
            logger.error(f"Error executing orders on {current_date}: {str(e)}")
            self.execution_errors.append({
                'date': current_date,
                'error': str(e)
            })
    
    def _execute_fill_in_portfolio(self, fill: Fill, execution_date: datetime):
        """Execute a fill in the portfolio"""
        try:
            # Convert fill to portfolio trade
            quantity = fill.quantity if fill.order_id else 0
            
            # Get the original order to determine side
            order = self.order_manager.get_order(fill.order_id)
            if not order:
                logger.error(f"Cannot find order {fill.order_id} for fill")
                return
            
            # Adjust quantity for sell orders
            if order.side == OrderSide.SELL:
                quantity = -quantity
            
            # Execute trade in portfolio
            success = self.portfolio_manager.execute_trade(
                symbol=fill.symbol,
                quantity=quantity,
                price=fill.price,
                commission=fill.commission,
                timestamp=execution_date,
                order_id=fill.order_id
            )
            
            if success:
                # Record completed trade
                trade_record = {
                    'order_id': fill.order_id,
                    'symbol': fill.symbol,
                    'side': order.side.value,
                    'quantity': abs(quantity),
                    'price': fill.price,
                    'commission': fill.commission,
                    'slippage': fill.slippage,
                    'timestamp': execution_date,
                    'trade_value': abs(quantity) * fill.price,
                    'net_cash_flow': -quantity * fill.price - fill.commission
                }
                
                # Calculate P&L if this closes/reduces a position
                if order.side == OrderSide.SELL:
                    position = self.portfolio_manager.get_position(fill.symbol)
                    if position:
                        # This is a simplified P&L calculation
                        trade_record['pnl'] = (fill.price - position.avg_cost) * abs(quantity)
                    else:
                        trade_record['pnl'] = 0
                else:
                    trade_record['pnl'] = 0  # Opening position, no realized P&L yet
                
                self.executed_trades.append(trade_record)
                
                logger.debug(f"Portfolio trade executed: {order.side.value} {abs(quantity)} {fill.symbol} @ {fill.price:.2f}")
            
            else:
                logger.error(f"Failed to execute trade in portfolio: {fill.symbol}")
                
        except Exception as e:
            logger.error(f"Error executing fill in portfolio: {str(e)}")
    
    def get_completed_trades(self) -> List[Dict]:
        """Get all completed trades"""
        return self.executed_trades.copy()
    
    def get_trade_summary(self, symbol: str = None) -> Dict:
        """Get trade summary statistics"""
        trades = self.executed_trades
        
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
        
        if not trades:
            return {}
        
        # Calculate summary statistics
        total_trades = len(trades)
        buy_trades = [t for t in trades if t['side'] == 'BUY']
        sell_trades = [t for t in trades if t['side'] == 'SELL']
        
        total_volume = sum(t['trade_value'] for t in trades)
        total_commission = sum(t['commission'] for t in trades)
        total_slippage = sum(t['slippage'] for t in trades)
        
        # P&L statistics (only for sell trades)
        pnl_trades = [t for t in sell_trades if 'pnl' in t]
        winning_trades = [t for t in pnl_trades if t['pnl'] > 0]
        losing_trades = [t for t in pnl_trades if t['pnl'] < 0]
        
        summary = {
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_volume': total_volume,
            'total_commission': total_commission,
            'total_slippage': total_slippage,
            'avg_trade_size': total_volume / total_trades if total_trades > 0 else 0,
            'avg_commission_per_trade': total_commission / total_trades if total_trades > 0 else 0
        }
        
        if pnl_trades:
            total_pnl = sum(t['pnl'] for t in pnl_trades)
            summary.update({
                'total_pnl': total_pnl,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(pnl_trades) if pnl_trades else 0,
                'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                'largest_win': max(t['pnl'] for t in winning_trades) if winning_trades else 0,
                'largest_loss': min(t['pnl'] for t in losing_trades) if losing_trades else 0
            })
            
            # Profit factor
            gross_profit = sum(t['pnl'] for t in winning_trades)
            gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            summary['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return summary
    
    def get_execution_errors(self) -> List[Dict]:
        """Get execution errors"""
        return self.execution_errors.copy()
    
    def reset(self):
        """Reset execution engine state"""
        self.executed_trades.clear()
        self.execution_errors.clear()
        logger.info("ExecutionEngine reset to initial state")

class AdvancedExecutionEngine(ExecutionEngine):
    """Advanced execution engine with market impact and realistic fills"""
    
    def __init__(self, portfolio_manager: PortfolioManager, order_manager: OrderManager,
                 execution_delay: int = 0, market_impact: bool = True,
                 volume_limit: float = 0.1, impact_factor: float = 0.001):
        super().__init__(portfolio_manager, order_manager, execution_delay, market_impact)
        self.volume_limit = volume_limit  # Max % of daily volume to trade
        self.impact_factor = impact_factor  # Market impact factor
        
    def _calculate_market_impact(self, order: Order, current_data: pd.Series) -> float:
        """Calculate market impact based on order size vs volume"""
        if not self.market_impact:
            return 0.0
        
        try:
            daily_volume = current_data.get('volume', 0)
            if daily_volume <= 0:
                return self.impact_factor  # Default impact if no volume data
            
            # Calculate order as percentage of daily volume
            order_volume_ratio = order.remaining_quantity / daily_volume
            
            # Impact increases with square root of volume ratio
            impact = self.impact_factor * (order_volume_ratio ** 0.5)
            
            # Cap impact at reasonable level
            return min(impact, 0.05)  # Max 5% impact
            
        except Exception:
            return self.impact_factor
    
    def _split_large_order(self, order: Order, current_data: pd.Series) -> List[float]:
        """Split large orders to reduce market impact"""
        daily_volume = current_data.get('volume', 0)
        if daily_volume <= 0:
            return [order.remaining_quantity]
        
        max_quantity = daily_volume * self.volume_limit
        
        if order.remaining_quantity <= max_quantity:
            return [order.remaining_quantity]
        
        # Split into smaller chunks
        num_chunks = int(order.remaining_quantity / max_quantity) + 1
        chunk_size = order.remaining_quantity / num_chunks
        
        chunks = [chunk_size] * (num_chunks - 1)
        chunks.append(order.remaining_quantity - sum(chunks))  # Remainder
        
        return chunks
    
    def _execute_order_with_impact(self, order: Order, execution_price: float, 
                                  execution_time: datetime, market_data: Dict[str, pd.DataFrame]) -> List[Fill]:
        """Execute order with market impact consideration"""
        fills = []
        
        try:
            # Get current market data
            if order.symbol not in market_data:
                return fills
            
            data = market_data[order.symbol]
            available_dates = data.index[data.index <= execution_time]
            if len(available_dates) == 0:
                return fills
            
            latest_date = available_dates[-1]
            current_data = data.loc[latest_date]
            
            # Calculate market impact
            market_impact = self._calculate_market_impact(order, current_data)
            
            # Split large orders
            quantity_chunks = self._split_large_order(order, current_data)
            
            # Execute each chunk
            for i, chunk_quantity in enumerate(quantity_chunks):
                # Adjust price for market impact (impact increases with each chunk)
                impact_adjustment = market_impact * (i + 1) * 0.5  # Diminishing impact
                
                if order.side == OrderSide.BUY:
                    adjusted_price = execution_price * (1 + impact_adjustment)
                else:
                    adjusted_price = execution_price * (1 - impact_adjustment)
                
                # Calculate slippage
                slippage_amount = adjusted_price * self.order_manager.slippage_rate
                if order.side == OrderSide.BUY:
                    final_price = adjusted_price + slippage_amount
                else:
                    final_price = adjusted_price - slippage_amount
                
                final_price = max(final_price, 0.01)  # Ensure positive price
                
                # Calculate commission
                trade_value = chunk_quantity * final_price
                commission = trade_value * self.order_manager.commission_rate
                
                # Create fill
                fill = Fill(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    quantity=chunk_quantity,
                    price=final_price,
                    timestamp=execution_time,
                    commission=commission,
                    slippage=slippage_amount * chunk_quantity,
                    notes=f"Chunk {i+1}/{len(quantity_chunks)}, impact={impact_adjustment:.4f}"
                )
                
                fills.append(fill)
                
                # Update order state
                order.filled_quantity += chunk_quantity
                order.remaining_quantity -= chunk_quantity
                order.commission += commission
                order.slippage += fill.slippage
                
                # Update average fill price
                total_filled_value = order.avg_fill_price * (order.filled_quantity - chunk_quantity)
                total_filled_value += final_price * chunk_quantity
                order.avg_fill_price = total_filled_value / order.filled_quantity
            
            # Update order status
            if order.remaining_quantity <= 0:
                order.status = order_manager.OrderStatus.FILLED
                order.filled_at = execution_time
            else:
                order.status = order_manager.OrderStatus.PARTIAL
            
        except Exception as e:
            logger.error(f"Error executing order with impact: {str(e)}")
        
        return fills