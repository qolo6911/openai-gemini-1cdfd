from typing import Dict

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

from core.live.risk_manager import RiskManager


class LiveExecutor:
    def __init__(self, symbol: str = 'XAUUSD'):
        self.symbol = symbol
        self.risk_manager = RiskManager()
    
    def execute_signal(self, signal: Dict) -> Dict:
        if mt5 is None:
            return {'status': 'error', 'message': 'MetaTrader5 module not available'}
        
        order_type = mt5.ORDER_TYPE_BUY if signal['action'] == 'LONG' else mt5.ORDER_TYPE_SELL
        lot_size = self.risk_manager.calculate_position_size(signal['sl_distance'])
        
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': self.symbol,
            'volume': lot_size,
            'type': order_type,
            'price': signal['price'],
            'sl': signal['stop_loss'],
            'tp': signal['take_profit'],
            'deviation': 20,
            'magic': 123456,
            'comment': 'AI Trading System',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {'status': 'success', 'ticket': result.order}
        return {'status': 'error', 'code': result.retcode}
