import os
import smtplib
import schedule
import time
from datetime import datetime
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from supabase import create_client, Client
import pdfkit
from collections import defaultdict

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération des clés depuis les variables d'environnement
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
EMAIL_SENDER = os.getenv("EMAIL_SENDER")       # Adresse email de l'expéditeur
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")   # Mot de passe ou clé d'application
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")   # Adresse email du destinataire

# Création d'une instance Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fonction pour récupérer les données depuis la table "Achats" dans Supabase
def fetch_data():
    return supabase.table('Achats').select("*").execute().data or []

# Fonction pour générer un PDF à partir des données récupérées
def generate_pdf(data):
    # Calcul du montant total des achats
    total = sum(item.get("MontantAchat", 0) for item in data)

    # Regrouper les quantités reçues par produit
    qte_by_product = defaultdict(float)
    for item in data:
        produit = item.get("DesignationArticle", "Inconnu")
        qte_by_product[produit] += item.get("QteRecue", 0)

    # Sélectionner les 3 produits les plus reçus
    top_3 = sorted(qte_by_product.items(), key=lambda x: x[1], reverse=True)[:3]

    # Date actuelle formatée pour affichage dans le rapport
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Chargement du modèle HTML Jinja2 depuis le dossier du script
    TEMPLATE_DIR = os.path.dirname(__file__)
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("rapport.html")

    # Rendu HTML avec les données passées au template
    html_out = template.render(
        achats=data,
        total=total,
        top_3=top_3,
        date=current_date
    )

    # Configuration de wkhtmltopdf pour générer le PDF
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    output_path = os.path.join(TEMPLATE_DIR, "rapport.pdf")

    # Génération du fichier PDF à partir du HTML
    pdfkit.from_string(html_out, output_path, configuration=config)

    return output_path  # Retourner le chemin du fichier PDF généré

# Fonction pour envoyer le PDF généré par email
def send_email(pdf_path):
    msg = EmailMessage()
    msg["Subject"] = "Rapport des Achats"            # Sujet de l'email
    msg["From"] = EMAIL_SENDER                       # Expéditeur
    msg["To"] = EMAIL_RECEIVER                       # Destinataire
    msg.set_content("Veuillez trouver ci-joint le rapport PDF des achats.")  # Corps du message

    # Ajouter le PDF en pièce jointe
    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="rapport.pdf")

    # Envoi de l'email via un serveur SMTP sécurisé (Gmail ici)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Connexion
        smtp.send_message(msg)                    # Envoi de l'email

# Tâche principale : récupérer, générer et envoyer
def job():
    data = fetch_data()
    pdf = generate_pdf(data)
    send_email(pdf)

# Planifier l'exécution du job tous les lundis à 09:00
schedule.every().monday.at("09:00").do(job)

# Boucle infinie pour garder le script en attente des tâches planifiées
while True:
    schedule.run_pending()  # Exécuter si une tâche est due
    time.sleep(60)          # Attendre 60 secondes avant de revérifier