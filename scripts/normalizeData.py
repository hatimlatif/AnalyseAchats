import pandas as pd
from scripts.cleaningData import cleanData


def normalizeDF(ogPath, saveDirectory):
    # Lire le fichier CSV original à partir du chemin donné
    df = pd.read_csv(ogPath)

    # Nettoyer le DataFrame en utilisant la fonction cleanData (suppression de NaN, conversion de types, etc.)
    df = cleanData(df)

    # Extraire les colonnes nécessaires pour le tableau des ventes (Achats)
    sales_df = df[['NumBonPese', 'DesignationArticle', 'DateBR',
                   'CodeFournisseur', 'NomBateau', 'QteRecue', 'QteFacturée',
                   'Qualite', 'Moule', 'PU', 'MontantAchat']]

    # Créer le tableau des fournisseurs en supprimant les doublons et en réinitialisant les index
    suppliers_df = df[['CodeFournisseur', 'DesignationFournisseur']].drop_duplicates().reset_index(drop=True)

    # Créer le tableau des articles (produits) en supprimant les doublons et en réinitialisant les index
    articles_df = df[['DesignationArticle', 'Famille']].drop_duplicates().reset_index(drop=True)

    # Calculer le chiffre d'affaires (CA) total par produit (somme de MontantAchat groupée par DesignationArticle)
    ca_df = df.groupby('DesignationArticle')['MontantAchat'].sum().reset_index()

    # Renommer la colonne 'MontantAchat' en 'CA' (chiffre d'affaires)
    ca_df.rename(columns={'MontantAchat': 'CA'}, inplace=True)

    # Fusionner les informations de CA avec les articles pour inclure le CA dans le tableau des produits
    articles_df = articles_df.merge(ca_df, on='DesignationArticle', how='left')

    # Enregistrer le tableau des ventes dans un fichier CSV nommé "Achats.csv" dans le répertoire spécifié
    sales_df.to_csv(f"{saveDirectory}/Achats.csv", index=False)

    # Enregistrer le tableau des fournisseurs dans "Fournisseurs.csv"
    suppliers_df.to_csv(f"{saveDirectory}/Fournisseurs.csv", index=False)

    # Enregistrer le tableau des produits (avec famille + CA) dans "Produits.csv"
    articles_df.to_csv(f"{saveDirectory}/Produits.csv", index=False)
