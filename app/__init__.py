from flask import Flask
import os

# Création de l’application Flask (l'objet principal de l’application)
app = Flask(__name__)

# Configuration de la clé secrète
# Elle est récupérée depuis les variables d’environnement
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Importation des routes de l’application (après la création de l'app pour éviter les import circulaires)
from app import routes
