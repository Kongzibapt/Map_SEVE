import base64
import streamlit as st
import pandas as pd
import folium
import tempfile
from geopy.geocoders import Nominatim
import time

# Configuration de l'application
st.set_page_config(page_title="Générateur de Carte", layout="wide")

# Titre de l'application
st.title("🗺️ Générateur de Carte Interactive")

# Liste des antennes avec leur latitude, longitude et niveau de zoom
antenne_zones = {
    "National": {"location": [46.603354, 1.888334], "zoom": 6},
    "AURA": {"location": [45.7485, 4.8467], "zoom": 8},
    "BFC": {"location": [47.0202, 4.8579], "zoom": 8},
    "Bretagne": {"location": [48.2020, -2.8885], "zoom": 7},
    "Corse": {"location": [41.9290, 9.0197], "zoom": 9},
    "CVDL": {"location": [47.3490, 1.5000], "zoom": 8},
    "Grand Est": {"location": [48.4775, 7.9474], "zoom": 7},
    "HDF": {"location": [50.6292, 3.0573], "zoom": 8},
    "IDF": {"location": [48.8566, 2.3522], "zoom": 10},
    "La Réunion": {"location": [-21.1151, 55.5364], "zoom": 9},
    "Normandie": {"location": [49.4144, 0.6943], "zoom": 8},
    "Nouvelle-Aquitaine": {"location": [44.8397, -0.5807], "zoom": 7},
    "Occitanie Montpellier": {"location": [43.6117, 3.8767], "zoom": 9},
    "Occitanie Toulouse": {"location": [43.6047, 1.4442], "zoom": 9},
    "PACA": {"location": [43.9333, 6.9167], "zoom": 8},
    "PDL": {"location": [47.3490, -0.6000], "zoom": 7}
}

# Ajouter une bannière en haut de la page
with st.expander("📍 Comment utiliser cette application ?"):
    st.markdown("""
        <style>
            .banner {
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }
                
            ol {
                margin-left: 20px;
            }
            
            ul {
                margin-left: 40px;
            }
        </style>
        <div class="banner">
            <ol>
                <li><strong>Sélectionner une antenne</strong> : Choisissez une antenne pour centrer la carte dessus (facultatif). Si vous ne souhaitez afficher que les informations de votre antenne, à vous de filtrer en conséquence.</li>
                <li><strong>Importer votre fichier Excel</strong> : Téléchargez un fichier contenant les données à afficher sur la carte.</li>
                    <ul>
                        <li>Le nom de la feuille doit être le même que celui de la colonne des informations à afficher. (Ex : "Cités éducatives" pour afficher les données de la colonne "Cités éducatives").</li>
                        <li>La feuille doit avoir au moins deux colonnes : Le nom ds informations à afficher et une colonne "Ville".</li>
                        <li>Si une feuille contient des informations de Longitude et Latitude, la génération de la carte sera immédiate, sinon il faut compter quelques secondes.</li>
                        <li>Si une feuille contient des colonnes supplémentaires, elles seront ignorées.</li>
                    </ul>
                <li><strong>Personnaliser l'apparence</strong> : Choisissez une couleur et une icône pour chaque feuille de votre fichier.</li>
                <li><strong>Générer la carte</strong> : Cliquez sur "Générer la carte" pour afficher la carte interactive.</li>
                <li><strong>Télécharger la carte</strong> : Une fois la carte créée, téléchargez-la en cliquant sur le lien.</li>
                <li><strong>Modifier la carte</strong> : Vous devez appuyer à nouveau sur "Générer la carte" pour prendre en compte les modifications.</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)

# Sélection de l'antenne
antenne_selected = st.selectbox("Sélectionnez une antenne", list(antenne_zones.keys()))

# Centre et zoom de la carte en fonction de l'antenne sélectionnée
location = antenne_zones[antenne_selected]["location"]
zoom = antenne_zones[antenne_selected]["zoom"]

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
        "darkblue": "🔵 Bleu", "red": "🔴 Rouge", "green": "🟢 Vert",
        "purple": "🟣 Violet", "orange": "🟠 Orange", 
        "pink": "🌹 Rose"
    }
    
    icon_options = {
        "info": "ℹ️ Info", "flag": "🚩 Drapeau",
        "star": "⭐ Étoile", "globe": "🌍 Globe",
        "home": "🏠 Maison", "university": "🎓 Université", 
        "building": "🏛️ Construction",
        "user": "👤 Utilisateur",
        "map-pin": "📍 Marqueur",
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
        m = folium.Map(location=location, zoom_start=zoom)  # Centrer et zoomer en fonction de l'antenne

        # Régler le type de carte
        folium.TileLayer('CartoDB.Voyager').add_to(m)
        
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
