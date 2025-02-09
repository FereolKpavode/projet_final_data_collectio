import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import base64
import re
import plotly.express as px
import os

# 🔹 Configuration de la page en mode large
st.set_page_config(layout="wide")

# 🔹 Étendre les tableaux en pleine largeur avec du CSS
st.markdown("""
    <style>
        .stDataFrame { width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

# 🔹 Fonction de scraping avec mise en cache
@st.cache_data(ttl=3600)  # TTL (Time to Live) de 1h pour éviter une mise en cache trop longue
def scrape_data(num_pages, page_type):
    data = []  # Liste pour stocker les données

    # Scraper la première page
    url_1 = f'https://sn.coinafrique.com/categorie/{page_type}'
    try:
        res = requests.get(url_1)
        res.raise_for_status()  # Vérification de l'état de la réponse
        soup = bs(res.text, 'html.parser')
        containers = soup.find_all('div', class_='col s6 m4 l3')

        for container in containers:
            try:
                # Récupérer l'URL du produit
                url_container = container.find('a', class_='card-image ad__card-image waves-block waves-light')['href']
                url_complet = 'https://sn.coinafrique.com' + url_container
                res_c = requests.get(url_complet)
                res_c.raise_for_status()
                soup_c = bs(res_c.text, 'html.parser')

                # Extraire les informations
                V1 = soup_c.find('h1', class_="title title-ad hide-on-large-and-down").text.strip()
                V2 = soup_c.find('p', class_="price").text.strip().replace('CFA', '').replace(" ", "")

                V3_html = soup_c.find('p', class_='extras')
                valign_spans = V3_html.find_all('span', class_='valign-wrapper')
                V3 = valign_spans[1].get_text(strip=True) if len(valign_spans) > 1 else "N/A"

                V4_soup = soup_c.find('div', class_='swiper-wrapper')
                divs_with_images = V4_soup.find_all('div', style=re.compile(r'background-image'))
                image_urls = [re.search(r'url\((.+?)\)', div['style']).group(1).strip('"') for div in divs_with_images if re.search(r'url\((.+?)\)', div['style'])]

                # Ajouter les données à la liste
                data.append({'type habits': V1, 'prix': V2, 'adresse': V3, 'image_lien': image_urls})
            except Exception as e:
                st.error(f"Erreur dans le scraping d'un produit: {e}")
        
        # Scraper les pages suivantes
        for page_num in range(2, num_pages + 1):
            url_p = f'https://sn.coinafrique.com/categorie/{page_type}?page={page_num}'
            res = requests.get(url_p)
            res.raise_for_status()
            soup = bs(res.text, 'html.parser')
            containers = soup.find_all('div', class_='col s6 m4 l3')

            for container in containers:
                try:
                    # Récupérer l'URL du produit
                    url_container = container.find('a', class_='card-image ad__card-image waves-block waves-light')['href']
                    url_complet = 'https://sn.coinafrique.com' + url_container
                    res_c = requests.get(url_complet)
                    res_c.raise_for_status()
                    soup_c = bs(res_c.text, 'html.parser')

                    # Extraire les informations
                    V1 = soup_c.find('h1', class_="title title-ad hide-on-large-and-down").text.strip()
                    V2 = soup_c.find('p', class_="price").text.strip().replace('CFA', '').replace(" ", "")

                    V3_html = soup_c.find('p', class_='extras')
                    valign_spans = V3_html.find_all('span', class_='valign-wrapper')
                    V3 = valign_spans[1].get_text(strip=True) if len(valign_spans) > 1 else "N/A"

                    V4_soup = soup_c.find('div', class_='swiper-wrapper')
                    divs_with_images = V4_soup.find_all('div', style=re.compile(r'background-image'))
                    image_urls = [re.search(r'url\((.+?)\)', div['style']).group(1).strip('"') for div in divs_with_images if re.search(r'url\((.+?)\)', div['style'])]

                    # Ajouter les données à la liste
                    data.append({'type habits': V1, 'prix': V2, 'adresse': V3, 'image_lien': image_urls})
                except Exception as e:
                    st.error(f"Erreur dans le scraping d'un produit: {e}")

    except Exception as e:
        st.error(f"Erreur dans le scraping de la page principale: {e}")

    # Convertir la liste de données en DataFrame
    df = pd.DataFrame(data)
    return df[['type habits', 'prix', 'adresse', 'image_lien']]

# 🔹 Fonction pour charger le fichier CSV en toute sécurité
def load_csv_safely(filepath, encoding="utf-8"):
    """Charge un fichier CSV s'il existe, sinon retourne un DataFrame vide."""
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath, sep=';', encoding=encoding)
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du chargement du fichier {filepath}: {e}")
            return pd.DataFrame()
    else:
        st.warning(f"⚠️ Le fichier {filepath} est introuvable.")
        return pd.DataFrame()

# 🔹 Fonction pour afficher les données en toute sécurité
def load_data(dataframe, title, key):
    """Affiche les données en pleine largeur avec un bouton interactif."""
    if st.button(title, key=key):
        st.subheader(f'📊 Dimensions des données - {title}')
        st.write(f'**{dataframe.shape[0]}** lignes et **{dataframe.shape[1]}** colonnes.')
        st.dataframe(dataframe, use_container_width=True, height=600)

# 🔹 Fonction principale de l'application
def main():
    st.markdown("<h1 style='text-align: center;'>Application de Scraping de Données</h1>", unsafe_allow_html=True)

    st.sidebar.title('🔹 Menu de navigation')
    num_pages = st.sidebar.slider("Nombre de pages à scraper", 1, 50, 5)

    page_type = st.sidebar.radio("📌 Choisissez une action :", 
                                 ['Scraper des données', 'Télécharger les données', 'Dashboard des données', 'Remplir le formulaire'])

    if page_type == 'Scraper des données':
        categories = ['vetements-homme', 'chaussures-homme', 'vetements-enfants', 'chaussures-enfants']

        # Création des colonnes pour afficher les boutons horizontalement
        col1, col2, col3, col4 = st.columns(4)

        # Vérifier quel bouton est cliqué et lancer le scraping
        if col1.button("👕 Scraper Vêtements Homme"):
            df_vetements_homme = scrape_data(num_pages, 'vetements-homme')
            st.subheader("📊 Données scrappées - Vêtements Homme")
            st.dataframe(df_vetements_homme, use_container_width=True, height=600)

        if col2.button("👞 Scraper Chaussures Homme"):
            df_chaussures_homme = scrape_data(num_pages, 'chaussures-homme')
            st.subheader("📊 Données scrappées - Chaussures Homme")
            st.dataframe(df_chaussures_homme, use_container_width=True, height=600)

        if col3.button("👕 Scraper Vêtements Enfants"):
            df_vetements_enfants = scrape_data(num_pages, 'vetements-enfants')
            st.subheader("📊 Données scrappées - Vêtements Enfants")
            st.dataframe(df_vetements_enfants, use_container_width=True, height=600)

        if col4.button("👟 Scraper Chaussures Enfants"):
            df_chaussures_enfants = scrape_data(num_pages, 'chaussures-enfants')
            st.subheader("📊 Données scrappées - Chaussures Enfants")
            st.dataframe(df_chaussures_enfants, use_container_width=True, height=600)

    elif page_type == 'Télécharger les données':
        st.write("## 📂 Sélectionnez une catégorie pour afficher les données")
        
        # Création des colonnes pour les boutons de sélection
        col1, col2, col3, col4 = st.columns(4)

        # Vérifier quel bouton est cliqué et afficher le DataFrame correspondant
        if col1.button("👕 Vêtements Homme"):
            df = load_csv_safely('data/vetements_homme.csv', encoding='ISO-8859-1')
            st.subheader("📊 Données - Vêtements Homme")
            st.dataframe(df, use_container_width=True, height=600)

        if col2.button("👞 Chaussures Homme"):
            df = load_csv_safely('data/Chaussure_hommes.csv', encoding='ISO-8859-1')
            st.subheader("📊 Données - Chaussures Homme")
            st.dataframe(df, use_container_width=True, height=600)

        if col3.button("👕 Vêtements Enfants"):
            df = load_csv_safely('data/vetements_enfants.csv')
            st.subheader("📊 Données - Vêtements Enfants")
            st.dataframe(df, use_container_width=True, height=600)

        if col4.button("👟 Chaussures Enfants"):
            df = load_csv_safely('data/chaussures_enfants.csv', encoding='ISO-8859-1')
            st.subheader("📊 Données - Chaussures Enfants")
            st.dataframe(df, use_container_width=True, height=600)

    elif page_type == 'Dashboard des données':
        st.write("## 📊 Tableau de Bord Interactif")
            
        # Sélection de la catégorie de page à scraper
        categorie = st.selectbox("Sélectionnez une catégorie de produits :", 
                                  ['vetements-homme', 'chaussures-homme', 'vetements-enfants', 'chaussures-enfants'])
        
        # Sélection du nombre de pages à scraper
        num_pages_dashboard = st.slider("Sélectionnez le nombre de pages à scraper :", 1, 50, 5)
        
        # Utilisation des données scrappées en fonction de la sélection
        df = scrape_data(num_pages=num_pages_dashboard, page_type=categorie)
        
        if df.empty:
            st.warning("⚠️ Aucune donnée trouvée pour l'affichage du tableau de bord.")
        else:
            df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
            
            # Analyse descriptive
            st.write("### Statistiques générales")
            st.write(df.describe())
            
            # Graphique interactif des prix
            st.write("### Distribution des Prix")
            fig_hist = px.histogram(df, x="prix", nbins=20, title="Répartition des prix", color_discrete_sequence=['blue'])
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Filtrage dynamique
            min_price, max_price = int(df['prix'].min()), int(df['prix'].max())
            price_range = st.slider("Filtrer par prix", min_value=min_price, max_value=max_price, value=(min_price, max_price))
            df_filtered = df[(df['prix'] >= price_range[0]) & (df['prix'] <= price_range[1])]
            
            # Top 5 des produits les plus chers
            top_5 = df_filtered.nlargest(5, 'prix')
            st.write("### Top 5 des produits les plus chers")
            fig_top5 = px.bar(top_5, x="type habits", y="prix", title="Produits les plus chers", color_discrete_sequence=['red'])
            st.plotly_chart(fig_top5, use_container_width=True)
            
            # Répartition géographique
            st.write("### Répartition des produits par localisation")
            fig_adresse = px.pie(df_filtered, names="adresse", title="Répartition des produits par adresse")
            st.plotly_chart(fig_adresse, use_container_width=True)
            
            # Affichage des données filtrées
            st.write("### Données Filtrées")
            st.dataframe(df_filtered, use_container_width=True, height=600)

    elif page_type == 'Remplir le formulaire':
        st.write("## 📝 Formulaire d'évaluation")
        st.markdown("""<iframe src="https://ee.kobotoolbox.org/i/FF8lCL1P" width="100%" height="600px"></iframe>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()