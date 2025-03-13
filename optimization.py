import backtrader as bt
import logging
import multiprocessing as mp
import csv
import datetime
from data_loader import fetch_data
from strategy import TrendFollowingStrategy

logger = logging.getLogger(__name__)

def run_single_optimization(args):
    """
    Executes a backtest using a given set of parameters for TrendFollowingStrategy.
    Parameters:
      - ticker, start_date, end_date, cash: basic backtest parameters
      - fast_ma: fast moving average period (for trend following)
      - slow_ma: slow moving average period (for trend following)
    Returns a tuple containing:
      (fast_ma, slow_ma, score, total_return, drawdown, params_tested)
    """
    ticker, start_date, end_date, cash, fast_ma, slow_ma = args
    cerebro = bt.Cerebro(maxcpus=1)  # Prevent multiprocessing conflicts
    cerebro.broker.setcash(cash)
    cerebro.optstrategy(
        TrendFollowingStrategy,
        fast_ma_period=[fast_ma],
        slow_ma_period=[slow_ma]
    )

    # Fetch market data
    data_df = fetch_data(ticker, start_date, end_date)
    if data_df is None or data_df.empty:
        logger.warning(f"No data available for {ticker}. Skipping this optimization.")
        return (fast_ma, slow_ma, 0, 0, 100, "No data")

    data = bt.feeds.PandasData(dataname=data_df)
    cerebro.adddata(data)

    results = cerebro.run()
    starting_value = cash
    ending_value = cerebro.broker.getvalue()
    total_return = (ending_value - starting_value) / starting_value * 100

    # Retrieve drawdown via analyzer; default to 100% if not available.
    try:
        drawdown = results[0][0].analyzers.drawdown.get_analysis().max.drawdown
    except Exception:
        drawdown = 100  # Set a high drawdown to penalize failing cases

    # Combined score: higher total return and lower drawdown yield a higher score.
    score = total_return / max(1, drawdown)
    params_tested = f"fast_ma_period={fast_ma}, slow_ma_period={slow_ma}"
    logger.info(f"Parameters: {params_tested}, Total Return={total_return:.2f}%, DrawDown={drawdown:.2f}%, Score={score:.2f}")
    
    return (fast_ma, slow_ma, score, total_return, drawdown, params_tested)

def run_optimization(ticker="AAPL", start_date="2018-01-01", end_date="2023-01-01", cash=100000):
    """
    Optimizes hyperparameters via Grid Search for TrendFollowingStrategy:
      - fast_ma_period: [5, 7, 10, 12, 15, 20, 25, 30, 35, 50, 60, 75]
      - slow_ma_period: [15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200] (must be greater than fast_ma_period)
    Uses multiprocessing to parallelize tests, limits the number of processes,
    and automatically saves results to a CSV file with a timestamp.
    Returns the best configuration based on a combined score (total_return/drawdown).
    """
    param_grid = [
        (ticker, start_date, end_date, cash, fast_ma, slow_ma)
        for fast_ma in [5, 7, 10, 12, 15, 20, 25, 30, 35, 50, 60, 75]
        for slow_ma in [15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200] if slow_ma > fast_ma
    ]
    
    num_processes = max(mp.cpu_count() // 2, 1)
    with mp.Pool(processes=num_processes) as pool:
        results = pool.map(run_single_optimization, param_grid)

    if not results:
        logger.warning("No valid optimization results.")
        best = None
    else:
        best = max(results, key=lambda x: x[2])
        logger.info(f"Best parameters: fast_ma_period={best[0]}, slow_ma_period={best[1]} with Score={best[2]:.2f}, Total Return={best[3]:.2f}%, DrawDown={best[4]:.2f}%")
    
    # Save results to CSV
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    csv_filename = f"optimization_results_{timestamp}.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["fast_ma_period", "slow_ma_period", "score", "total_return", "drawdown", "params_tested"])
        for res in results:
            writer.writerow(res)
    logger.info(f"Optimization results saved in {csv_filename}")

    return best

if __name__ == "__main__":
    best_params = run_optimization()
    if best_params:
        print(f"Best parameters: fast_ma_period={best_params[0]}, slow_ma_period={best_params[1]} with Score={best_params[2]:.2f}")
    else:
        print("No optimal parameters found.")
