import os
import pickle
import time
import yfinance as yf
import pandas as pd
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = "data_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_path(ticker: str, start_date: str, end_date: str) -> str:
    """Returns the cache file path corresponding to the given parameters."""
    filename = f"{ticker}_{start_date}_{end_date}.pkl"
    return os.path.join(CACHE_DIR, filename)

def fetch_data(ticker: str, start_date: str, end_date: str, force_refresh: bool = False, cache_days: int = 1) -> pd.DataFrame:
    """
    Downloads or loads cached historical data for a given ticker from Yahoo Finance.

    ### Parameters:
    - ticker: Stock or ETF symbol (e.g., "AAPL").
    - start_date, end_date: Date range in "YYYY-MM-DD" format.
    - *orce_refresh: If `True`, forces data reload by deleting the existing cache.
    - cache_days: Validity period of the cache in days (default: 1 day).

    ### Returns:
    - A DataFrame with properly formatted columns: `['Close', 'High', 'Low', 'Open', 'Volume']`.
    """
    try:
        start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    except Exception as e:
        error_msg = f"Erreur de format de date. Utilisez le format 'YYYY-MM-DD'. Détail de l'erreur : {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    cache_path = get_cache_path(ticker, start_date, end_date)
    if force_refresh and os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("Cache supprimé suite à l'option force_refresh.")

    if os.path.exists(cache_path):
        cache_age = time.time() - os.path.getmtime(cache_path)
        if cache_age <= cache_days * 86400:
            logger.info(f"Chargement des données depuis le cache pour {ticker}")
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        else:
            logger.info("Cache expiré, rechargement des données.")
            os.remove(cache_path)

    logger.info(f"Téléchargement des données pour {ticker} du {start_date} au {end_date}")
    data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
    if data.empty:
        error_msg = f"Aucune donnée récupérée pour {ticker}. Vérifiez le ticker ou la disponibilité de l'API Yahoo Finance."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # --- Formatage des données ---
    # Gestion du multi-index :
    # Dans l'output, Yahoo Finance renvoie des colonnes avec un MultiIndex comme suit :
    #  Level 0: ['Price', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
    #  Level 1: ['AAPL', 'AAPL', 'AAPL', 'AAPL', 'AAPL', 'AAPL', 'AAPL']
    # On souhaite obtenir un DataFrame avec des colonnes simples.
    if isinstance(data.columns, pd.MultiIndex):
        # Extraire le niveau 0 (les noms des champs)
        fields = list(data.columns.get_level_values(0))
        logger.info(f"Multi-index détecté pour {ticker}. Champs extraits : {fields}")
        # On construit un mapping : on veut ignorer le champ "Price"
        mapping = {}
        for col in data.columns:
            field = col[0]
            if field != "Price" and field not in mapping:
                mapping[field] = col
        # Création d'un nouveau DataFrame avec l'ordre souhaité
        desired_order = ["Close", "High", "Low", "Open", "Volume"]
        new_data = pd.DataFrame(index=data.index)
        for field in desired_order:
            if field in mapping:
                new_data[field] = data[mapping[field]]
            elif field == "Close" and "Adj Close" in mapping:
                logger.warning(f"'Close' absent pour {ticker}; utilisation de 'Adj Close' à la place.")
                new_data[field] = data[mapping["Adj Close"]]
            else:
                error_msg = f"Colonne '{field}' manquante pour {ticker}."
                logger.error(error_msg)
                raise ValueError(error_msg)
        data = new_data
    else:
        # Cas d'un index simple : si "Close" est absent mais "Adj Close" est présent, renommer
        if "Close" not in data.columns and "Adj Close" in data.columns:
            logger.warning(f"'Close' absent pour {ticker}; renommage de 'Adj Close' en 'Close'.")
            data.rename(columns={"Adj Close": "Close"}, inplace=True)
        # Conserver uniquement les colonnes souhaitées dans l'ordre désiré
        desired_order = ["Close", "High", "Low", "Open", "Volume"]
        missing = set(desired_order) - set(data.columns)
        if missing:
            error_msg = f"Les données récupérées pour {ticker} sont incomplètes. Colonnes manquantes: {missing}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        data = data[desired_order]
    
    data.index = pd.to_datetime(data.index)
    if data.isnull().values.any():
        logger.warning("Valeurs manquantes détectées. Application d'un forward fill.")
        data.fillna(method="ffill", inplace=True)
    # --- Fin du formatage des données ---
    
    with open(cache_path, "wb") as f:
        pickle.dump(data, f)
    return data
