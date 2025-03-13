import matplotlib.pyplot as plt
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def plot_portfolio_vs_buy_and_hold(dates, portfolio_values, price_series, ticker, log_scale=False):
    """
    Trace l'évolution du portefeuille comparée à une stratégie buy & hold.
    Possibilité d'afficher en échelle logarithmique et d'ajouter des annotations pour les entrées/sorties.
    """
    try:
        # Si 'dates' est un DatetimeIndex, utilisez-le directement par indexation
        initial_investment = portfolio_values.iloc[0]
        buy_hold = price_series / price_series.iloc[0] * initial_investment

        plt.figure(figsize=(12, 6))
        plt.plot(dates, portfolio_values, label='Stratégie', marker='o')
        plt.plot(dates, buy_hold, label='Buy & Hold', linestyle='--')
        plt.title(f"Évolution du portefeuille vs Buy & Hold - {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Valeur")
        if log_scale:
            plt.yscale("log")
        # Utiliser l'indexation classique sur 'dates'
        plt.annotate("BUY", xy=(dates[0], portfolio_values.iloc[0]),
                     xytext=(dates[0], portfolio_values.iloc[0]*1.05),
                     arrowprops=dict(facecolor='green', shrink=0.05), color='green')
        plt.annotate("SELL", xy=(dates[-1], portfolio_values.iloc[-1]),
                     xytext=(dates[-1], portfolio_values.iloc[-1]*0.95),
                     arrowprops=dict(facecolor='red', shrink=0.05), color='red')
        plt.legend()
        plt.grid(True)
        # Sauvegarder le graphique dans le dossier 'reports'
        plt.savefig(f"reports/{ticker}_performance.png")
        plt.close()
    except Exception as e:
        logger.error("Erreur lors du tracé du portefeuille vs Buy & Hold: " + str(e))

def plot_daily_returns_histogram(daily_returns, ticker):
    """
    Affiche un histogramme des rendements journaliers.
    """
    try:
        plt.figure(figsize=(10, 6))
        plt.hist(daily_returns, bins=50, alpha=0.75, color='blue')
        plt.title(f"Histogramme des rendements journaliers - {ticker}")
        plt.xlabel("Rendement journalier")
        plt.ylabel("Fréquence")
        plt.grid(True)
        plt.show()
    except Exception as e:
        logger.error("Erreur lors du tracé de l'histogramme des rendements: " + str(e))

def plot_drawdown(drawdown_series, ticker):
    """
    Affiche le drawdown maximal sous forme de graphique.
    """
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(drawdown_series.index, drawdown_series.values, color='red')
        plt.title(f"Drawdown maximal - {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Drawdown (%)")
        plt.grid(True)
        plt.show()
    except Exception as e:
        logger.error("Erreur lors du tracé du drawdown: " + str(e))

