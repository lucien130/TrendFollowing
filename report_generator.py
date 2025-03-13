from fpdf import FPDF
import logging
import os

logger = logging.getLogger(__name__)

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 18)  # Augmentation de la taille du titre
        self.cell(0, 10, self.title, ln=True, align="C", border=1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_pdf_report(strategy_metrics, ticker, output_file="report.pdf"):
    """
    Génère un rapport PDF résumant les indicateurs de performance et intégrant des graphiques.
    - Affiche les métriques dans un tableau.
    - Intègre le graphique de performance si disponible.
    Le rapport est sauvegardé dans le dossier "reports".
    """
    try:
        # Création du dossier "reports" s'il n'existe pas
        reports_folder = "reports"
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)
        
        # Construire le chemin complet pour le fichier de sortie
        output_path = os.path.join(reports_folder, output_file)

        pdf = PDFReport()
        pdf.title = f"Rapport de Performance - {ticker}"
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Performances de la Stratégie", ln=True, border=1, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", size=12)
        for key, value in strategy_metrics.items():
            pdf.cell(50, 10, f"{key}:", border=1)
            pdf.cell(0, 10, f"{value}", border=1, ln=True)
        
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Résumé des Performances", ln=True, border=1, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        summary = (f"La stratégie sur {ticker} a généré un rendement total de "
                   f"{strategy_metrics.get('Rendement Total (%)', 'N/A')}% avec un Sharpe Ratio de "
                   f"{strategy_metrics.get('Ratio de Sharpe', 'N/A')} et un drawdown maximal de "
                   f"{strategy_metrics.get('Drawdown Max (%)', 'N/A')}%.")
        pdf.multi_cell(0, 10, summary, border=1)
        
        # Intégrer le graphique de performance s'il existe
        image_path = os.path.join(reports_folder, f"{ticker}_performance.png")
        if os.path.exists(image_path):
            pdf.ln(10)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Graphique de Performance", ln=True, border=1, align="C")
            pdf.image(image_path, x=10, w=180)
        else:
            logger.warning(f"Image du graphique non trouvée pour {ticker} dans le dossier '{reports_folder}'.")
        
        pdf.output(output_path)
        logger.info(f"Rapport PDF généré: {output_path}")
    except Exception as e:
        logger.error("Erreur lors de la génération du rapport PDF: " + str(e))

if __name__ == "__main__":
    sample_metrics = {
        "Rendement Total (%)": 15.5,
        "Ratio de Sharpe": 1.2,
        "Drawdown Max (%)": 10.0,
        "Nombre de Trades": 25,
        "Test t (statistique)": 2.5,
        "Test p (valeur p)": 0.01,
        "Rendement Net (%)": 15.0
    }
    generate_pdf_report(sample_metrics, "AAPL", "sample_report.pdf")
