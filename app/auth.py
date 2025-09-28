from functools import wraps
from flask import session, redirect, url_for, g
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Chargement des variables d’environnement depuis le fichier .env
load_dotenv()

# Récupération de l’URL et de la clé secrète de Supabase depuis les variables d’environnement
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


# Fonction pour obtenir l’utilisateur actuellement connecté à partir du token stocké dans la session
def current_user():
    # Récupération du token d'authentification depuis la session
    token = session.get("access_token")

    # Création d’une instance du client Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Si aucun token n’est présent, aucun utilisateur n’est connecté
    if not token:
        return None

    try:
        # Récupération des informations de l’utilisateur à partir du token
        user = supabase.auth.get_user(token).user
        return user
    except Exception:
        # En cas d’erreur (ex. token invalide), la session est supprimée et aucun utilisateur n’est retourné
        session.clear()
        return None


# Décorateur pour restreindre l’accès aux routes aux utilisateurs connectés uniquement
def login_required(fn):
    @wraps(fn)  # Conserve le nom et la docstring de la fonction originale
    def wrapper(*args, **kwargs):
        # Récupère l’utilisateur connecté et le stocke dans g (objet global de Flask)
        g.user = current_user()

        # Si aucun utilisateur connecté, redirige vers la page de login
        if g.user is None:
            return redirect(url_for("login"))

        # Sinon, exécute la fonction décorée normalement
        return fn(*args, **kwargs)

    return wrapper
