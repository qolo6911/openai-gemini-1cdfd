class RiskManager:
    def __init__(self, risk_percent: float = 0.5, max_daily_loss: float = 2.0):
        self.risk_percent = risk_percent / 100.0
        self.max_daily_loss = max_daily_loss / 100.0
    
    def calculate_position_size(self, sl_distance: float, account_balance: float = 10000) -> float:
        risk_amount = account_balance * self.risk_percent
        position_size = risk_amount / sl_distance
        return min(max(position_size, 0.01), 10.0)
    
    def check_daily_loss(self, daily_pnl: float, account_balance: float) -> bool:
        loss_percent = abs(daily_pnl) / account_balance
        return loss_percent < self.max_daily_loss
