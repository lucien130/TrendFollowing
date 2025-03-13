import numpy as np
import logging
from math import sqrt
from scipy import stats

logger = logging.getLogger(__name__)

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calculate the Sharpe ratio from actual daily returns.
    If volatility is zero, return 0.0 to avoid division by zero.
    """
    excess_returns = returns - risk_free_rate
    std = np.std(excess_returns)
    if std == 0:
        return 0.0
    return np.mean(excess_returns) / std * sqrt(252)

def perform_statistical_test(returns):
    """
    Performs a Student's t-test to check if the mean of daily returns is significantly different from zero.
    """
    t_stat, p_value = stats.ttest_1samp(returns, 0.0)
    return t_stat, p_value

def analyze_performance(cerebro, strat, ticker, sharpe_analysis, drawdown_analysis):
    """
    Calculates and returns multiple performance indicators:
    - Total return (%)
    - Sharpe ratio based on actual returns
    - Maximum drawdown (%)
    - Number of trades executed
    - Statistical test on daily returns
    """
    starting_value = cerebro.broker.startingcash
    ending_value = cerebro.broker.getvalue()
    total_return = (ending_value - starting_value) / starting_value * 100

    # Récupération des retours journaliers via l'analyzer TimeReturn
    timereturn = strat.analyzers.timereturn.get_analysis()
    returns = np.array(list(timereturn.values()))
    sharpe_ratio = calculate_sharpe_ratio(returns)
    t_stat, p_value = perform_statistical_test(returns)

    try:
        max_drawdown = drawdown_analysis.max.drawdown
    except Exception:
        max_drawdown = 0.0
    trade_count = getattr(strat, 'trade_count', 0)

    performance_metrics = {
        "Ticker": ticker,
        "Rendement Total (%)": round(total_return, 2),
        "Ratio de Sharpe": round(sharpe_ratio, 2),
        "Drawdown Max (%)": round(max_drawdown, 2),
        "Nombre de Trades": trade_count,
        "Test t (statistique)": round(t_stat, 2),
        "Test p (valeur p)": round(p_value, 4)
    }
    logger.info(f"Analyse de performance pour {ticker} terminée: {performance_metrics}")
    return performance_metrics
