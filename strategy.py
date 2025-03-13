import backtrader as bt
import logging

logger = logging.getLogger(__name__)

class TrendFollowingStrategy(bt.Strategy):
    params = (
        ('fast_ma_period', 12),           # Période de la moyenne mobile rapide
        ('slow_ma_period', 25),           # Période de la moyenne mobile lente
        ('risk_per_trade', 0.03),         # Fraction du portefeuille à risquer par trade
        ('atr_period', 10),               # Période pour le calcul de l'ATR
        ('atr_smooth_period', 3),         # Période pour lisser l'ATR
        ('trailing_stop_multiplier', 2.2),# Multiplicateur pour le trailing stop basé sur l'ATR
        ('min_stop_loss', 0.5),           # Stop-loss minimum
        ('commission', 0.001),            # Commission (0.1%)
    )

    def __init__(self):
        # Moyennes mobiles pour détecter la tendance
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_ma_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_ma_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # ATR et ATR lissé pour la gestion du stop-loss
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.smoothed_atr = bt.indicators.SimpleMovingAverage(self.atr, period=self.params.atr_smooth_period)

        # Variables pour la gestion des ordres et du trailing stop
        self.order = None
        self.entry_price = None
        self.current_stop = None
        self.trade_count = 0

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # Attente d'exécution
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"ACHAT exécuté : Prix = {order.executed.price:.2f}, Taille = {order.executed.size}")
                self.entry_price = order.executed.price
                self.trade_count += 1
                # Calcul du stop-loss initial basé sur l'ATR lissé
                stop_loss_distance = max(self.smoothed_atr[0] * self.params.trailing_stop_multiplier, self.params.min_stop_loss)
                self.current_stop = self.entry_price - stop_loss_distance
            elif order.issell():
                self.log(f"VENTE exécutée : Prix = {order.executed.price:.2f}, Taille = {order.executed.size}")
                self.entry_price = None
                self.current_stop = None
                self.trade_count += 1
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Ordre annulé / marge insuffisante / rejeté")
        self.order = None

    def next(self):
        # Ne pas agir si un ordre est en attente
        if self.order:
            return

        # Si aucune position n'est détenue, vérifier le signal d'achat
        if not self.position:
            # Signal d'achat : la moyenne rapide croise au-dessus de la moyenne lente (crossover positif)
            if self.crossover[0] > 0:
                self.log("Signal d'achat détecté (crossover positif)")
                portfolio_value = self.broker.getvalue()
                risk_amount = portfolio_value * self.params.risk_per_trade
                # Calculer la distance de stop-loss basée sur ATR
                stop_loss_distance = max(self.smoothed_atr[0] * self.params.trailing_stop_multiplier, self.params.min_stop_loss)
                size = int(risk_amount / (stop_loss_distance * (1 + self.params.commission)))
                if size <= 0:
                    self.log("Taille calculée <= 0, aucun trade n'est passé")
                    return
                self.log(f"Taille de position calculée : {size} actions")
                try:
                    self.order = self.buy(size=size)
                except Exception as e:
                    self.log("Erreur lors de l'exécution de l'ordre d'achat: " + str(e))
        else:
            # Si une position est détenue, vérifier le signal de vente (crossover négatif)
            if self.crossover[0] < 0:
                self.log("Signal de vente détecté (crossover négatif)")
                try:
                    self.order = self.sell(size=self.position.size)
                except Exception as e:
                    self.log("Erreur lors de l'exécution de l'ordre de vente: " + str(e))
            else:
                # Mise à jour du trailing stop : le stop ne doit jamais baisser
                new_stop = self.data.close[0] - self.smoothed_atr[0] * self.params.trailing_stop_multiplier
                if self.current_stop is None:
                    self.current_stop = self.entry_price - max(self.smoothed_atr[0] * self.params.trailing_stop_multiplier, self.params.min_stop_loss)
                elif new_stop > self.current_stop:
                    self.log(f"Mise à jour du trailing stop: {self.current_stop:.2f} -> {new_stop:.2f}")
                    self.current_stop = new_stop
                # Si le prix descend en dessous du trailing stop, vendre
                if self.data.close[0] < self.current_stop:
                    self.log("Stop loss déclenché par le trailing stop")
                    try:
                        self.order = self.sell(size=self.position.size)
                    except Exception as e:
                        self.log("Erreur lors de l'exécution de l'ordre de vente (trailing stop): " + str(e))
