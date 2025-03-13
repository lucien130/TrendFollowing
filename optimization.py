import backtrader as bt
import logging
import multiprocessing as mp
import csv
import datetime
from data_loader import fetch_data
from strategy import AdvancedMeanReversionStrategy

logger = logging.getLogger(__name__)

def run_single_optimization(args):
    """Fonction pour exécuter un backtest avec un ensemble de paramètres donné."""
    ticker, start_date, end_date, cash, sma_period, bb_dev = args
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(cash)
    cerebro.optstrategy(
        AdvancedMeanReversionStrategy,
        sma_period=[sma_period],
        bb_dev=[bb_dev]
    )
    data_df = fetch_data(ticker, start_date, end_date)
    data = bt.feeds.PandasData(dataname=data_df)
    cerebro.adddata(data)
    results = cerebro.run()
    starting_value = cash
    ending_value = cerebro.broker.getvalue()
    total_return = (ending_value - starting_value) / starting_value * 100

    # Récupération du drawdown via analyzer, sinon une valeur par défaut
    try:
        drawdown = results[0][0].analyzers.drawdown.get_analysis().max.drawdown
    except Exception:
        drawdown = 1
    # Score combiné : total_return / max(1, drawdown)
    score = total_return / max(1, drawdown)
    params_testes = f"sma_period={sma_period}, bb_dev={bb_dev}"
    logger.info(f"Paramètres: {params_testes}, Total Return={total_return:.2f}%, DrawDown={drawdown:.2f}%, Score={score:.2f}")
    return (sma_period, bb_dev, score, total_return, drawdown, params_testes)

def run_optimization(ticker="AAPL", start_date="2018-01-01", end_date="2023-01-01", cash=100000):
    """
    Optimise via Grid Search les hyperparamètres :
      - sma_period : [10, 20, 50]
      - bb_dev : [1.5, 2.0, 2.5]
    Utilise multiprocessing pour paralléliser les tests, en limitant le nombre de processus.
    Sauvegarde automatiquement les résultats dans un fichier CSV avec un timestamp.
    Retourne la meilleure configuration selon un score combiné (total_return/drawdown).
    """
    param_grid = [(ticker, start_date, end_date, cash, sma, bb) for sma in [10, 20, 50] for bb in [1.5, 2.0, 2.5]]
    num_processes = max(mp.cpu_count() // 2, 1)
    with mp.Pool(processes=num_processes) as pool:
        results = pool.map(run_single_optimization, param_grid)

    if not results:
        logger.warning("Aucun résultat d'optimisation valide.")
        best = None
    else:
        best = max(results, key=lambda x: x[2])
        logger.info(f"Meilleurs paramètres: sma_period={best[0]}, bb_dev={best[1]} avec Score={best[2]:.2f}, Total Return={best[3]:.2f}%, DrawDown={best[4]:.2f}%")
    
    # Générer un timestamp pour le nom du fichier
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    csv_filename = f"optimization_results_{timestamp}.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["sma_period", "bb_dev", "score", "total_return", "drawdown", "Params Testés"])
        for res in results:
            writer.writerow(res)
    logger.info(f"Résultats d'optimisation sauvegardés dans {csv_filename}")

    return best

if __name__ == "__main__":
    best_params = run_optimization()
    print(f"Meilleurs paramètres: sma_period={best_params[0]}, bb_dev={best_params[1]} avec Score={best_params[2]:.2f}")
