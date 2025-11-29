# -*- coding: utf-8 -*-
"""
Recherche de Bars à Jeux à Paris
Une application Streamlit pour trouver des bars à jeux à Paris et se connecter avec d'autres joueurs
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime
import os
import chardet

# Configuration de la page
st.set_page_config(page_title="Bars à Jeux Paris", page_icon="🎮", layout="wide")

# Custom CSS pour le thème bleu et les polices personnalisées
st.markdown("""
<style>
    /* Import fallback fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@700&family=Montserrat:wght@600&family=Open+Sans&display=swap');
    
    /* Titres principaux - Rockwell/Castellar avec fallback */
    h1 {
        font-family: 'Rockwell', 'Castellar', 'Roboto Slab', serif !important;
        color: #003366 !important;
        font-weight: bold !important;
    }
    
    /* Sous-titres - Eras Demi avec fallback */
    h2, h3 {
        font-family: 'Eras Demi ITC', 'Montserrat', sans-serif !important;
        color: #0066CC !important;
    }
    
    /* Corps de texte - Corbel avec fallback */
    p, div, span, label, input, textarea, select {
        font-family: 'Corbel', 'Open Sans', sans-serif !important;
    }
    
    /* Boutons bleus */
    .stButton>button {
        background-color: #1E90FF !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Corbel', 'Open Sans', sans-serif !important;
    }
    
    .stButton>button:hover {
        background-color: #0066CC !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #E6F3FF;
        border-radius: 8px 8px 0px 0px;
        font-family: 'Corbel', 'Open Sans', sans-serif !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E90FF !important;
        color: white !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #E6F3FF !important;
        border-radius: 8px !important;
        font-family: 'Corbel', 'Open Sans', sans-serif !important;
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser session state
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = []

if 'games_data' not in st.session_state:
    st.session_state.games_data = pd.DataFrame(columns=['bar_name', 'game'])

if 'game_requests' not in st.session_state:
    st.session_state.game_requests = []

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# Chemins des fichiers CSV
FORUM_CSV_PATH = os.path.join(os.path.dirname(__file__), 'forum_comments.csv')
GAME_REQUESTS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'game_requests.csv')

# Mapping des noms de fichiers CSV vers les noms de bars dans le GeoJSON
BAR_CSV_MAPPING = {
    'liste_jeux_aubonheurdesjeux.csv': 'Au Bonheur des Jeux',
    'liste_jeux_aude12.csv': 'Au Dé 12',
    'liste_jeux_goodgame.csv': 'The good game',
    'liste_jeux_larevanche.csv': 'La revanche',
    'liste_jeux_latavernedefwinax.csv': 'La Taverne De Fwinax',
    'liste_jeux_lenid.csv': 'Le nid cocon ludique',
    'liste_jeux_lesgentlemendujeu.csv': 'Les Gentlemen du Jeu',
    'liste_jeux_lesmauvaisjoueurs.csv': 'Les Mauvais Joueurs',
    'liste_jeux_loufoque.csv': 'Loufoque',
    'liste_jeux_meisia.csv': 'Café Meisia',
    'liste_jeux_oberjeux.csv': 'OberJeux',
    'liste_jeux_oya.csv': 'Oya Café',
}

# Fonction pour détecter l'encodage d'un fichier
def detect_encoding(file_path):
    """Détecte l'encodage d'un fichier en lisant les premiers octets"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

# Fonction pour charger les jeux depuis les fichiers CSV
@st.cache_data
def load_games_from_csv():
    """Charge tous les jeux depuis les fichiers CSV avec détection d'encodage"""
    games_list = []
    csv_folder = os.path.join(os.path.dirname(__file__), 'Scraping Liste Jeux')
    
    if not os.path.exists(csv_folder):
        return pd.DataFrame(columns=['bar_name', 'game'])
    
    for csv_file, bar_name in BAR_CSV_MAPPING.items():
        csv_path = os.path.join(csv_folder, csv_file)
        if os.path.exists(csv_path):
            try:
                encoding = detect_encoding(csv_path)
                try:
                    df = pd.read_csv(csv_path, sep=';', encoding=encoding)
                except:
                    for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            df = pd.read_csv(csv_path, sep=';', encoding=enc)
                            break
                        except:
                            continue
                
                if 'Nom du jeu' in df.columns:
                    for game_name in df['Nom du jeu'].dropna().unique():
                        games_list.append({'bar_name': bar_name, 'game': str(game_name)})
            except Exception as e:
                st.warning(f"⚠️ Erreur lors du chargement de {csv_file}: {e}")
    
    return pd.DataFrame(games_list)

# Fonction pour charger les commentaires du forum
def load_forum_comments():
    """Charge les commentaires du forum depuis le fichier CSV"""
    if os.path.exists(FORUM_CSV_PATH):
        try:
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []

# Fonction pour sauvegarder un commentaire
def save_forum_comment(post):
    """Sauvegarde un commentaire dans le fichier CSV"""
    try:
        if os.path.exists(FORUM_CSV_PATH):
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
        else:
            df = pd.DataFrame(columns=['username', 'bar', 'game', 'when', 'message', 'timestamp'])
        
        new_row = pd.DataFrame([post])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {e}")

# Fonction pour charger les requêtes de jeux
def load_game_requests():
    """Charge les requêtes de jeux depuis le fichier CSV"""
    if os.path.exists(GAME_REQUESTS_CSV_PATH):
        try:
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []

# Fonction pour sauvegarder une requête de jeu
def save_game_request(request):
    """Sauvegarde une requête de jeu dans le fichier CSV"""
    try:
        if os.path.exists(GAME_REQUESTS_CSV_PATH):
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
        else:
            df = pd.DataFrame(columns=['timestamp', 'username', 'bar_name', 'game_name', 'action_type', 'description', 'status'])
        
        new_row = pd.DataFrame([request])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {e}")

# Fonction pour approuver une requête
def approve_game_request(index):
    """Approuve une requête et ajoute le jeu à la base"""
    request = st.session_state.game_requests[index]
    new_row = pd.DataFrame({'bar_name': [request['bar_name']], 'game': [request['game_name']]})
    st.session_state.games_data = pd.concat([st.session_state.games_data, new_row], ignore_index=True)
    request['status'] = 'approved'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')

# Fonction pour rejeter une requête
def reject_game_request(index):
    """Rejette une requête"""
    request = st.session_state.game_requests[index]
    request['status'] = 'rejected'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')

# Charger les données au démarrage
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()

if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()

if len(st.session_state.game_requests) == 0:
    st.session_state.game_requests = load_game_requests()

# SIDEBAR - Admin Login
with st.sidebar:
    st.markdown("### 👤 Profil Administrateur")
    if not st.session_state.admin_logged_in:
        admin_password = st.text_input("Mot de passe Admin:", type="password", key="admin_pw")
        if st.button("Se connecter"):
            if admin_password == "admin123":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
    else:
        st.success("✅ Connecté en tant qu'administrateur")
        if st.button("Se déconnecter"):
            st.session_state.admin_logged_in = False
            st.rerun()

# En-tête
st.title("🎮 Recherche de Bars à Jeux à Paris")
st.markdown("*Trouvez votre prochaine destination de jeu et connectez-vous avec d'autres joueurs !*")
st.markdown("---")

# Charger les données géographiques
@st.cache_data
def load_data():
    gdf_bar = gpd.read_file("liste_bar_OK.geojson")
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # Créer les onglets (sans admin si pas connecté)
    if st.session_state.admin_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte et Recherche", "🎮 Liste des Jeux", "💬 Forum Communautaire", "🔧 Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["🗺️ Carte et Recherche", "🎮 Liste des Jeux", "💬 Forum Communautaire"])
    
    # ONGLET 1: Carte et Recherche
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("🔍 Trouver un Bar")
            
            search_name = st.text_input("Rechercher par nom :", placeholder="Entrez le nom du bar...")
            
            # Trier les arrondissements par ordre croissant
            arrondissements = sorted(gdf_bar['Arrondissement'].dropna().unique(), key=lambda x: int(x) if str(x).isdigit() else 999)
            selected_arrond = st.selectbox("Filtrer par arrondissement :", ["Tous"] + [str(a) for a in arrondissements])
            
            if not st.session_state.games_data.empty:
                all_games = sorted(st.session_state.games_data['game'].unique())
                selected_game = st.selectbox("Rechercher par jeu :", ["Tous les Jeux"] + all_games)
            else:
                selected_game = "Tous les Jeux"
                st.info("💡 Allez dans l'onglet 'Liste des Jeux' pour ajouter des jeux !")
            
            # Appliquer les filtres
            filtered_gdf = gdf_bar.copy()
            has_filter = False
            
            if search_name:
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].str.contains(search_name, case=False, na=False)]
                has_filter = True
            
            if selected_arrond != "Tous":
                filtered_gdf = filtered_gdf[filtered_gdf['Arrondissement'].astype(str) == selected_arrond]
                has_filter = True
            
            if selected_game != "Tous les Jeux" and not st.session_state.games_data.empty:
                bars_with_game = st.session_state.games_data[st.session_state.games_data['game'] == selected_game]['bar_name'].unique()
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].isin(bars_with_game)]
                has_filter = True
                st.success(f"Trouvé {len(filtered_gdf)} bar(s) avec {selected_game}")
            
            # Afficher la liste SEULEMENT si un filtre est appliqué
            if has_filter and len(filtered_gdf) > 0:
                st.info(f"Affichage de {len(filtered_gdf)} bar(s)")
                st.markdown("---")
                st.markdown("**Bars affichés :**")
                for idx, row in filtered_gdf.iterrows():
                    # Compter les jeux pour ce bar
                    bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                    game_count = len(bar_games)
                    
                    st.markdown(f"""<div style='background-color: #E6F3FF; padding: 12px; border-radius: 8px; margin-bottom: 10px;'>
                    <h4 style='margin:0; color: #0066CC;'>📍 {row['Nom']}</h4>
                    </div>""", unsafe_allow_html=True)
                    
                    with st.container():
                        if pd.notna(row['Adresse']):
                            st.write(f"**Adresse :** {row['Adresse']}")
                        if pd.notna(row['Arrondissement']):
                            st.write(f"**Arrondissement :** {row['Arrondissement']}")
                        if pd.notna(row['Code postal']):
                            st.write(f"**Code postal :** {row['Code postal']}")
                        if pd.notna(row['Métro']):
                            st.write(f"**Métro :** {row['Métro']}")
                        if pd.notna(row['Téléphone']):
                            st.write(f"**Téléphone :** {row['Téléphone']}")
                        if pd.notna(row['Site']):
                            st.write(f"**Site Web :** {row['Site']}")
                        
                        # Afficher seulement le nombre de jeux
                        if game_count > 0:
                            st.write(f"**🎮 Nombre de jeux :** {game_count}")
                        st.markdown("---")
            elif has_filter:
                st.warning("Aucun bar trouvé avec les filtres sélectionnés.")
        
        with col1:
            st.subheader("🗺️ Carte des Bars à Jeux")
            if has_filter and len(filtered_gdf) > 0:
                st.map(filtered_gdf[['lat', 'lon']])
            elif not has_filter:
                # Afficher la carte sans la liste
                st.map(gdf_bar[['lat', 'lon']])
                st.info("💡 Cliquez sur les points de la carte et utilisez les filtres pour voir les détails des bars")
            else:
                st.warning("Aucun bar trouvé.")
    
    # ONGLET 2: Liste des Jeux
    with tab2:
        st.subheader("🎮 Liste des Jeux par Bar")
        st.markdown("*Recherchez des jeux et demandez l'ajout de nouveaux jeux*")
        
        # Section de recherche
        st.markdown("### 🔍 Rechercher des Jeux")
        col1, col2 = st.columns(2)
        
        with col1:
            search_bar_filter = st.selectbox("Filtrer par Bar :", ["Tous les Bars"] + sorted(gdf_bar['Nom'].tolist()))
        
        with col2:
            search_game_text = st.text_input("Rechercher un jeu :", placeholder="Tapez le nom d'un jeu...")
        
        # Filtrer les jeux
        filtered_games = st.session_state.games_data.copy()
        
        if search_bar_filter != "Tous les Bars":
            filtered_games = filtered_games[filtered_games['bar_name'] == search_bar_filter]
        
        if search_game_text:
            filtered_games = filtered_games[filtered_games['game'].str.contains(search_game_text, case=False, na=False)]
        
        # Afficher les résultats avec expanders par bar
        if not filtered_games.empty:
            st.markdown(f"**{len(filtered_games)} jeu(x) trouvé(s)**")
            st.markdown("---")
            
            # Grouper par bar et utiliser des expanders
            for bar in filtered_games['bar_name'].unique():
                games = filtered_games[filtered_games['bar_name'] == bar]['game'].tolist()
                
                with st.expander(f"📍 {bar} ({len(games)} jeux)", expanded=False):
                    # Afficher les jeux en colonnes
                    cols_per_row = 3
                    for i in range(0, len(games), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, game in enumerate(games[i:i+cols_per_row]):
                            cols[j].write(f"🎮 {game}")
        else:
            st.info("Aucun jeu trouvé avec ces critères.")
        
        st.markdown("---")
        
        # Section de demande d'ajout
        st.markdown("### ➕ Demander l'Ajout d'un Jeu")
        st.info("💡 Votre demande sera envoyée à l'administrateur pour approbation.")
        
        with st.form("request_game_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                request_username = st.text_input("Votre Nom :", placeholder="Entrez votre nom")
                request_bar = st.selectbox("Sélectionner un Bar :", gdf_bar['Nom'].sort_values().tolist())
            
            with col2:
                request_game = st.text_input("Nom du Jeu :", placeholder="Tapez le nom du jeu")
                request_action = st.selectbox("Type de Demande :", ["Ajouter un nouveau jeu", "Modifier un jeu existant"])
            
            request_description = st.text_area("Description (optionnel) :", placeholder="Détails supplémentaires...")
            
            if st.form_submit_button("📤 Envoyer la Demande"):
                if request_username and request_game and request_bar:
                    request = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'username': request_username,
                        'bar_name': request_bar,
                        'game_name': request_game,
                        'action_type': 'add' if request_action == "Ajouter un nouveau jeu" else 'modify',
                        'description': request_description,
                        'status': 'pending'
                    }
                    st.session_state.game_requests.append(request)
                    save_game_request(request)
                    st.success("✅ Votre demande a été envoyée !")
                else:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires !")
        
        # Afficher les demandes de l'utilisateur
        st.markdown("---")
        st.markdown("### 📋 Mes Demandes")
        pending_requests = [r for r in st.session_state.game_requests if r['status'] == 'pending']
        approved_requests = [r for r in st.session_state.game_requests if r['status'] == 'approved']
        
        if pending_requests:
            st.info(f"📌 {len(pending_requests)} demande(s) en attente")
        if approved_requests:
            st.success(f"✅ {len(approved_requests)} demande(s) approuvée(s)")
    
    # ONGLET 3: Forum Communautaire
    with tab3:
        st.subheader("💬 Forum Communautaire")
        st.markdown("*Vous cherchez quelqu'un pour jouer ? Postez ici !*")
        
        # Section de création de post
        with st.form("new_post_form"):
            st.markdown("**Créer un Nouveau Post**")
            username = st.text_input("Votre Nom :", placeholder="Entrez votre nom")
            bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
            
            game_input_type = st.radio("Comment voulez-vous entrer le jeu ?", ["Taper le nom", "Sélectionner dans la liste"])
            
            if game_input_type == "Taper le nom":
                game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
            else:
                if not st.session_state.games_data.empty:
                    game_choice = st.selectbox("Jeu :", ["N'importe quel Jeu"] + sorted(st.session_state.games_data['game'].unique()))
                else:
                    game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
            
            date_time = st.text_input("Quand :", placeholder="ex: Demain 19h, Ce samedi")
            message = st.text_area("Message :", placeholder="Votre message...")
            
            submitted = st.form_submit_button("📤 Publier")
            
            if submitted:
                if username and message and game_choice:
                    post = {
                        'username': username,
                        'bar': bar_choice,
                        'game': game_choice,
                        'when': date_time,
                        'message': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.forum_posts.insert(0, post)
                    save_forum_comment(post)
                    st.success("✅ Post créé !")
                    st.rerun()
                else:
                    st.error("Veuillez remplir votre nom, votre message et le jeu !")
        
        st.markdown("---")
        st.markdown("**Posts Récents**")
        
        if len(st.session_state.forum_posts) == 0:
            st.info("Aucun post pour le moment. Soyez le premier à poster !")
        else:
            for idx, post in enumerate(st.session_state.forum_posts):
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{post['username']}** • {post['timestamp']}")
                        st.markdown(f"🎮 {post['game']} @ 📍 {post['bar']}")
                        if post.get('when'):
                            st.markdown(f"🕐 {post['when']}")
                        st.markdown(f"{post['message']}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{idx}"):
                            st.session_state.forum_posts.pop(idx)
                            try:
                                df = pd.DataFrame(st.session_state.forum_posts)
                                df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
                            except:
                                pass
                            st.rerun()
                    st.markdown("---")
    
    # ONGLET 4: Admin (SEULEMENT SI CONNECTÉ)
    if st.session_state.admin_logged_in:
        with tab4:
            st.subheader("🔧 Interface Administrateur")
            st.markdown("*Gérez les demandes d'ajout de jeux*")
            
            status_filter = st.selectbox("Filtrer par statut :", ["Tous", "En attente", "Approuvé", "Rejeté"])
            
            filtered_requests = st.session_state.game_requests.copy()
            if status_filter == "En attente":
                filtered_requests = [r for r in filtered_requests if r['status'] == 'pending']
            elif status_filter == "Approuvé":
                filtered_requests = [r for r in filtered_requests if r['status'] == 'approved']
            elif status_filter == "Rejeté":
                filtered_requests = [r for r in filtered_requests if r['status'] == 'rejected']
            
            st.markdown(f"**{len(filtered_requests)} requête(s)**")
            st.markdown("---")
            
            for idx, request in enumerate(filtered_requests):
                real_idx = st.session_state.game_requests.index(request)
                
                with st.expander(f"{'🔵' if request['status'] == 'pending' else '✅' if request['status'] == 'approved' else '❌'} {request['game_name']} @ {request['bar_name']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Date :** {request['timestamp']}")
                        st.write(f"**Utilisateur :** {request['username']}")
                        st.write(f"**Bar :** {request['bar_name']}")
                        st.write(f"**Jeu :** {request['game_name']}")
                        st.write(f"**Type :** {request['action_type']}")
                        if request['description']:
                            st.write(f"**Description :** {request['description']}")
                        st.write(f"**Statut :** {request['status']}")
                    
                    with col2:
                        if request['status'] == 'pending':
                            if st.button("✅", key=f"approve_{real_idx}"):
                                approve_game_request(real_idx)
                                st.success("Approuvé !")
                                st.rerun()
                            
                            if st.button("❌", key=f"reject_{real_idx}"):
                                reject_game_request(real_idx)
                                st.rerun()

except FileNotFoundError:
    st.error("⚠️ Fichier liste_bar_OK.geojson introuvable.")
except Exception as e:
    st.error(f"⚠️ Erreur : {str(e)}")

# Pied de page
st.markdown("---")
st.markdown("*Créé par Kalma et José bestie :)*")
