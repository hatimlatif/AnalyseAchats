from flask import render_template, request, flash, session, redirect, url_for
from supabase import create_client, Client
from app import app
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10
from bokeh.models import HoverTool, NumeralTickFormatter, CustomJSTickFormatter
from collections import defaultdict
from app.auth import login_required
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis .env
load_dotenv()

# Récupérer les clés Supabase à partir de .env
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


# Route de connexion
@app.route("/")
def redirectLogin():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # Création du client Supabase
    if session.get("access_token"):  # Si l'utilisateur est déjà connecté
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        # Récupération des données du formulaire
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            # Authentification via Supabase
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session["access_token"] = res.session.access_token  # Stockage du token dans la session
            flash("Bienvenue!", "success")  # Message de succès
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Invalid credentials", "danger")  # Message d’erreur
    return render_template("login.html")  # Affichage de la page login


# Route de déconnexion
@app.route("/logout")
def logout():
    session.clear()  # Suppression de toutes les données de session
    return redirect(url_for("login"))


# Tableau de bord principal
@app.route('/dashboard')
@login_required
def dashboard():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # Connexion Supabase

    # Récupération des produits et fournisseurs
    produits = supabase.table("Produits").select("*").execute().data or []
    fournisseurs = supabase.table("Fournisseurs").select("*").execute().data or []

    # Récupération des filtres de la requête (formulaire ou URL)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    fournisseur = request.args.get('fournisseur')
    article = request.args.get('article')
    montant_min = request.args.get('montant_min')
    montant_max = request.args.get('montant_max')

    # Construction des requêtes pour les tables Achats et AchatsBP
    query = supabase.table('Achats').select('*')
    queryBP = supabase.table('AchatsBP').select('*')

    # Application des filtres dynamiquement
    if date_from:
        query = query.filter('DateBR', 'gte', date_from)
        queryBP = queryBP.filter('DateBR', 'gte', date_from)
    if date_to:
        query = query.filter('DateBR', 'lte', date_to)
        queryBP = queryBP.filter('DateBR', 'lte', date_to)
    if fournisseur:
        query = query.filter('CodeFournisseur', 'ilike', f'%{fournisseur}%')
        queryBP = queryBP.filter('CodeFournisseur', 'ilike', f'%{fournisseur}%')
    if article:
        query = query.filter('DesignationArticle', 'ilike', f'%{article}%')
    if montant_min:
        query = query.gte('MontantAchat', float(montant_min))
    if montant_max:
        query = query.lte('MontantAchat', float(montant_max))

    # Exécution des requêtes filtrées
    achats = query.execute().data or []
    achatsBP = queryBP.execute().data or []

    # Calcul des totaux depuis AchatsBP
    totalPaye = sum(item["TotPaye"] for item in achatsBP)
    totalRecu = sum(item["TotRecu"] for item in achatsBP)
    totalFacture = sum(item["TotFacture"] for item in achatsBP)
    TotalEcartQ = sum(item["EcartQt"] for item in achatsBP)
    TotalEcartM = sum(item["EcartMontant"] for item in achatsBP)

    # Détermination de l’intervalle des montants
    all_achats = supabase.table('Achats').select('MontantAchat').execute().data or []
    minRange = min((achat["MontantAchat"] for achat in all_achats), default=0)
    maxRange = max((achat["MontantAchat"] for achat in all_achats), default=0)
    maxRange += 100

    js_format_code = """
        var num = tick.toFixed(2).replace('.', ',');
        return num.replace(/\\B(?=(\\d{3})+(?!\\d))/g, " ");
    """

    def get_colors(data_length):
        if data_length == 0:
            return []
        palette = Category10[10]
        return (palette * ((data_length // 10) + 1))[:data_length]

    # ---- GRAPHIQUE 1 : CA par produit ----
    ca_by_product = defaultdict(float)
    for achat in achats:
        ca_by_product[achat['DesignationArticle']] += achat['MontantAchat']

    product_names = list(ca_by_product.keys())

    p1 = figure(
        x_range=product_names,
        title="Chiffre d'affaires par Produit",
        toolbar_location=None, tools="hover",
        sizing_mode='stretch_both'
    )
    p1.vbar(
        x=product_names,
        top=list(ca_by_product.values()),
        width=0.9, color=get_colors(len(product_names))
    )
    p1.title.text_font_size = '16pt'
    p1.xaxis.major_label_orientation = 1
    p1.background_fill_color = "#f9f9f9"
    p1.outline_line_color = None
    p1.yaxis.formatter = CustomJSTickFormatter(code=js_format_code)
    p1.add_tools(
        HoverTool(tooltips=[("Produit", "@x"), ("CA", "@top{(0.00 a)}")], formatters={"@top": "numeral"}, mode='vline'))

    # ---- GRAPHIQUE 2 : Écarts par fournisseur ----
    ecarts_by_provider = defaultdict(float)
    for achat in achats:
        ecart = abs(achat.get("QteRecue", 0) - achat.get("QteFacturee", 0))
        ecarts_by_provider[achat['CodeFournisseur']] += ecart

    provider_names_g2 = list(ecarts_by_provider.keys())

    p2 = figure(
        x_range=provider_names_g2,
        title="Écarts par Fournisseur",
        toolbar_location=None, tools="hover",
        sizing_mode='stretch_both'
    )
    p2.vbar(
        x=provider_names_g2,
        top=list(ecarts_by_provider.values()),
        width=0.9, color=get_colors(len(provider_names_g2))
    )
    p2.title.text_font_size = '16pt'
    p2.xaxis.major_label_orientation = 1
    p2.background_fill_color = "#f9f9f9"
    p2.outline_line_color = None
    p2.yaxis.formatter = CustomJSTickFormatter(code=js_format_code)
    p2.add_tools(
        HoverTool(tooltips=[("Fournisseur", "@x"), ("Écart", "@top{(0.00 a)}")], formatters={"@top": "numeral"},
                  mode='vline'))

    # ---- GRAPHIQUE 3 : Qté vendue par produit ----
    qte_by_product = defaultdict(float)
    for achat in achats:
        qte_by_product[achat['DesignationArticle']] += achat['QteRecue']

    product_names_g3 = list(qte_by_product.keys())

    p3 = figure(
        x_range=product_names_g3,
        title="Produits les Plus Vendus",
        toolbar_location=None, tools="hover",
        sizing_mode='stretch_both'
    )
    p3.vbar(
        x=product_names_g3,
        top=list(qte_by_product.values()),
        width=0.9, color=get_colors(len(product_names_g3))
    )
    p3.title.text_font_size = '16pt'
    p3.xaxis.major_label_orientation = 1
    p3.background_fill_color = "#f9f9f9"
    p3.outline_line_color = None
    p3.yaxis.formatter = CustomJSTickFormatter(code=js_format_code)
    p3.add_tools(HoverTool(tooltips=[("Produit", "@x"), ("Qté", "@top{(0.00 a)}")], formatters={"@top": "numeral"},
                           mode='vline'))

    # ---- GRAPHIQUE 4 : Écart Quantité dans AchatsBP par fournisseur ----
    ecartqt_bp_by_provider = defaultdict(float)
    for row in achatsBP:
        code_f = row.get("CodeFournisseur", "NA")
        ecart_q = row.get("EcartQt", 0) or 0
        ecartqt_bp_by_provider[code_f] += ecart_q

    providers_bp = list(ecartqt_bp_by_provider.keys())
    ecart_vals_bp = list(ecartqt_bp_by_provider.values())

    p4 = figure(
        x_range=providers_bp,
        title="Écart Quantité par Fournisseur",
        toolbar_location=None,
        tools="hover",
        sizing_mode='stretch_both'
    )

    p4.vbar(
        x=providers_bp,
        top=ecart_vals_bp,
        width=0.9,
        color=get_colors(len(providers_bp))
    )
    p4.title.text_font_size = '16pt'
    p4.xaxis.major_label_orientation = 1
    p4.background_fill_color = "#f9f9f9"
    p4.outline_line_color = None
    p4.yaxis.formatter = CustomJSTickFormatter(code=js_format_code)
    p4.add_tools(
        HoverTool(tooltips=[("Fournisseur", "@x"), ("Écart Qt", "@top{(0.00 a)}")], formatters={"@top": "numeral"},
                  mode='vline'))

    # Génération des scripts HTML pour les graphiques
    script1, div1 = components(p1)
    script2, div2 = components(p2)
    script3, div3 = components(p3)
    script4, div4 = components(p4)

    # Rendu de la page dashboard avec les variables nécessaires
    return render_template("dashboard.html",
                           achats=achats,
                           achatsBP=achatsBP,
                           produits=produits,
                           fournisseurs=fournisseurs,
                           minRange=minRange,
                           maxRange=maxRange,
                           totalPaye=totalPaye,
                           totalFacture=totalFacture,
                           totalRecu=totalRecu,
                           TotalEcartM=TotalEcartM,
                           TotalEcartQ=TotalEcartQ,
                           script1=script1, div1=div1,
                           script2=script2, div2=div2,
                           script3=script3, div3=div3,
                           script4=script4, div4=div4
                           )
