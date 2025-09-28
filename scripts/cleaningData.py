import pandas as pd


def cleanData(df):
    # Supprimer les lignes contenant des valeurs manquantes, sauf dans les colonnes 'Moule' et 'Qualite'
    df = df.dropna(subset=[col for col in df.columns if (col != 'Moule' and col != 'Qualite')])

    # Convertir la colonne 'DateBR' en format datetime (gère les formats mixtes)
    df['DateBR'] = pd.to_datetime(df['DateBR'], format='mixed')

    # Convertir la colonne 'QteRecue' en numérique, en remplaçant les erreurs par NaN
    df['QteRecue'] = pd.to_numeric(df['QteRecue'], errors='coerce')

    # Convertir la colonne 'QteFacturée' en numérique, en remplaçant les erreurs par NaN
    df['QteFacturée'] = pd.to_numeric(df['QteFacturée'], errors='coerce')

    # Convertir la colonne 'PU' (Prix Unitaire) en numérique, erreurs remplacées par NaN
    df['PU'] = pd.to_numeric(df['PU'], errors='coerce')

    # Convertir la colonne 'MontantAchat' en numérique, erreurs remplacées par NaN
    df['MontantAchat'] = pd.to_numeric(df['MontantAchat'], errors='coerce')

    # Forcer la colonne 'NumBonPese' à être de type chaîne de caractères
    df['NumBonPese'] = df['NumBonPese'].astype(str)

    # Forcer la colonne 'CodeFournisseur' à être de type chaîne de caractères
    df['CodeFournisseur'] = df['CodeFournisseur'].astype(str)

    # Forcer la colonne 'DesignationFournisseur' à être de type chaîne de caractères
    df['DesignationFournisseur'] = df['DesignationFournisseur'].astype(str)

    # Forcer la colonne 'DesignationArticle' à être de type chaîne de caractères
    df['DesignationArticle'] = df['DesignationArticle'].astype(str)

    # Forcer la colonne 'Famille' à être de type chaîne de caractères
    df['Famille'] = df['Famille'].astype(str)

    # Forcer la colonne 'NomBateau' à être de type chaîne de caractères
    df['NomBateau'] = df['NomBateau'].astype(str)

    # Forcer la colonne 'Qualite' à être de type chaîne de caractères
    df['Qualite'] = df['Qualite'].astype(str)

    # Forcer la colonne 'Moule' à être de type chaîne de caractères
    df['Moule'] = df['Moule'].astype(str)

    # Créer une nouvelle colonne 'Ecart' représentant la différence entre 'QteRecue' et 'QteFacturée'
    df['Ecart'] = df['QteRecue'] - df['QteFacturée']

    # Retourner le DataFrame nettoyé
    return df
