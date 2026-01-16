from typing import Dict
import json


def generate_report(results: Dict, output_path: str = 'reports/backtest_report.json') -> None:
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
