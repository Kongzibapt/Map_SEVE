import base64
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import tempfile
import random
from geopy.geocoders import Nominatim
import time

# Configuration de l'application
st.set_page_config(page_title="Générateur de Carte", layout="wide")

# Titre de l'application
st.title("📍 Générateur de Carte Interactive")

# Upload du fichier Excel
uploaded_file = st.file_uploader("📂 Importer un fichier Excel", type=["xlsx"])

# Fonction pour obtenir la latitude et la longitude à partir d'une ville
def get_coordinates(city_name, retries=3, delay=2):
    geolocator = Nominatim(user_agent="MonAppCarte_Geocoding", timeout=10)
    for attempt in range(retries):
        try:
            location = geolocator.geocode(city_name)
            if location:
                return location.latitude, location.longitude
            else:
                return None, None
        except Exception as e:
            print(f"Tentative {attempt + 1} échouée: {e}")
            time.sleep(delay)  # Attendre avant de réessayer
    return None, None  # Retourner None si toutes les tentatives échouent

if uploaded_file:
    # Charger toutes les feuilles du fichier Excel
    xls = pd.ExcelFile(uploaded_file)
    
    # Définir les options de couleurs et icônes avec traductions et pastilles
    color_options = {
        "blue": "🔵 Bleu", "red": "🔴 Rouge", "green": "🟢 Vert",
        "purple": "🟣 Violet", "orange": "🟠 Orange", "darkblue": "🔵 Bleu Foncé",
        "cadetblue": "🔵 Bleu Cadet", "pink": "🎀 Rose"
    }
    
    icon_options = {
        "info": "ℹ️ Info", "cloud": "☁️ Nuage", "flag": "🚩 Drapeau",
        "star": "⭐ Étoile", "leaf": "🍃 Feuille", "globe": "🌍 Globe",
        "home": "🏠 Maison", "university": "🎓 Université"
    }
    
    # Stocker les sélections de l'utilisateur
    group_styles = {}
    
    # Affichage des options en colonnes
    cols = st.columns(2)
    for i, sheet_name in enumerate(xls.sheet_names):
        with cols[i % 2]:  # Alterner entre les deux colonnes
            st.subheader(f"⚙️ Paramètres pour {sheet_name}")
            color = st.selectbox(f"🎨 Couleur de {sheet_name}", list(color_options.keys()),
                                 format_func=lambda x: color_options[x],
                                 index=0)
            icon = st.selectbox(f"🔘 Icône de {sheet_name}", list(icon_options.keys()),
                                format_func=lambda x: icon_options[x],
                                index=0)
            group_styles[sheet_name] = {"color": color, "icon": icon}
    
    # Bouton unique pour générer et télécharger la carte
    if st.button("Générer la carte"):
        m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
        
        # Vérifier que chaque feuille contient les colonnes requises
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # Vérification de la présence des colonnes Longitude et Latitude
            if "Longitude" in df.columns and "Latitude" in df.columns:
                # Si les colonnes Longitude et Latitude sont présentes, on les utilise directement
                coordinates_available = True
            elif "Ville" in df.columns:
                # Si la colonne Ville est présente, on utilise geopy pour obtenir les coordonnées
                coordinates_available = False
            else:
                st.error(f"❌ La feuille '{sheet_name}' doit contenir les colonnes : 'Longitude', 'Latitude' ou 'Ville'")
                continue
            
            # Récupérer les choix de l'utilisateur
            color = group_styles[sheet_name]["color"]
            icon = group_styles[sheet_name]["icon"]
            
            # Créer un groupe de repères pour la feuille
            group_name = f'<span style="background-color:{color}; border-radius:50%; width:15px; height:15px; display:inline-block;"></span> {sheet_name}'
            group = folium.FeatureGroup(name=group_name)
            
            # Ajouter les marqueurs
            for _, row in df.iterrows():
                if coordinates_available:
                    # Si les coordonnées sont disponibles dans la feuille
                    latitude, longitude = row["Latitude"], row["Longitude"]
                else:
                    # Sinon, on récupère les coordonnées via geopy
                    city = row["Ville"]
                    latitude, longitude = get_coordinates(city)
                
                if latitude and longitude:
                    folium.Marker(
                        location=[latitude, longitude],
                        popup=row[sheet_name],
                        tooltip=row[sheet_name],
                        icon=folium.Icon(color=color, icon=icon, prefix="fa")
                    ).add_to(group)
            
            # Ajouter le groupe à la carte
            group.add_to(m)
        
        # Ajouter le contrôle des couches
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Sauvegarder la carte en fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            m.save(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                html_data = f.read()
                b64 = base64.b64encode(html_data).decode()
                href = f'<a href="data:file/html;base64,{b64}" download="carte_interactive.html">📥 Télécharger la carte</a>'
                st.markdown(href, unsafe_allow_html=True)
