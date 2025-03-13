import backtrader as bt
import logging
from data_loader import fetch_data
from strategy import TrendFollowingStrategy
from analysis import analyze_performance
from visualization import (
    plot_portfolio_vs_buy_and_hold,
    plot_daily_returns_histogram,
    plot_drawdown
)
from report_generator import generate_pdf_report
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_backtest_for_ticker(ticker, start_date, end_date, cash=100000):
    """
    Exécute le backtest pour un ticker donné et génère les graphiques ainsi qu'un rapport PDF.
    - Utilise les analyzers SharpeRatio, DrawDown et TimeReturn pour récupérer des métriques précises.
    - Calcule les retours journaliers via (1 + returns).cumprod() pour une performance cumulative correcte.
    - Ajoute une colonne "Rendement Net (%)" qui prend en compte les commissions.
    """
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addstrategy(TrendFollowingStrategy)

    # Ajout des analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')

    # Charger les données déjà formatées par data_loader
    data_df = fetch_data(ticker, start_date, end_date)
    data = bt.feeds.PandasData(dataname=data_df)
    cerebro.adddata(data)

    logger.info(f"Début du backtest pour {ticker}")
    results = cerebro.run()[0]
    logger.info(f"Backtest terminé pour {ticker}")

    # Récupération des analyzers
    sharpe_analysis = results.analyzers.sharpe.get_analysis()
    drawdown_analysis = results.analyzers.drawdown.get_analysis()
    timereturn = results.analyzers.timereturn.get_analysis()

    # Calcul des retours journaliers et de la valeur du portefeuille
    returns_series = pd.Series(list(timereturn.values()))
    portfolio_values = (1 + returns_series).cumprod() * cash
    dates = pd.to_datetime(list(timereturn.keys()))

    # Calcul des métriques de performance
    performance_metrics = analyze_performance(cerebro, results, ticker, sharpe_analysis, drawdown_analysis)
    # Correction ici : accéder directement à results (qui est la stratégie)
    trade_count = getattr(results, "trade_count", 0)
    net_return = performance_metrics["Rendement Total (%)"] - (trade_count * 0.001 * 100)
    performance_metrics["Rendement Net (%)"] = round(net_return, 2)

    # Visualisations avancées
    plot_portfolio_vs_buy_and_hold(dates, portfolio_values, data_df["Close"], ticker, log_scale=False)
    daily_returns = portfolio_values.pct_change().dropna()
    plot_daily_returns_histogram(daily_returns, ticker)
    drawdown_series = (portfolio_values / portfolio_values.cummax() - 1) * 100
    plot_drawdown(drawdown_series, ticker)

    # Génération du rapport PDF
    generate_pdf_report(performance_metrics, ticker, output_file=f"report_{ticker}.pdf")

    return performance_metrics

def run_multi_asset_backtest(tickers, start_date="2018-01-01", end_date="2023-01-01", cash=100000):
    """
    Exécute le backtest sur plusieurs actifs et retourne un rapport de performance par ticker.
    """
    all_metrics = {}
    for ticker in tickers:
        logger.info(f"--- Traitement de {ticker} ---")
        metrics = run_backtest_for_ticker(ticker, start_date, end_date, cash)
        all_metrics[ticker] = metrics
    return all_metrics

if __name__ == "__main__":
    tickers = ["AAPL", "TTE", "TSLA", "NVDA"]
    metrics_report = run_multi_asset_backtest(tickers)
    for ticker, metrics in metrics_report.items():
        print(f"Performance pour {ticker}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
