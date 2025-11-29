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

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@700&family=Montserrat:wght@600&family=Open+Sans&display=swap');
    
    h1 {
        font-family: 'Rockwell', 'Castellar', 'Roboto Slab', serif !important;
        color: #003366 !important;
        font-weight: bold !important;
    }
    
    h2, h3 {
        font-family: 'Eras Demi ITC', 'Montserrat', sans-serif !important;
        color: #0066CC !important;
    }
    
    p, div, span, label, input, textarea, select {
        font-family: 'Corbel', 'Open Sans', sans-serif !important;
    }
    
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
    
    .stAlert {
        border-radius: 8px !important;
    }
    
    /* Profile button styling */
    .profile-button {
        position: fixed;
        top: 60px;
        right: 20px;
        z-index: 999;
        background-color: #1E90FF;
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = []
if 'games_data' not in st.session_state:
    st.session_state.games_data = pd.DataFrame(columns=['bar_name', 'game'])
if 'game_requests' not in st.session_state:
    st.session_state.game_requests = []
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'show_admin_panel' not in st.session_state:
    st.session_state.show_admin_panel = False

# File paths
FORUM_CSV_PATH = os.path.join(os.path.dirname(__file__), 'forum_comments.csv')
GAME_REQUESTS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'game_requests.csv')

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

# Optimized: detect encoding once
@st.cache_data
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

# Optimized: cache game loading
@st.cache_data
def load_games_from_csv():
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
            except:
                pass
    
    return pd.DataFrame(games_list)

def load_forum_comments():
    if os.path.exists(FORUM_CSV_PATH):
        try:
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []

def save_forum_comment(post):
    try:
        if os.path.exists(FORUM_CSV_PATH):
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
        else:
            df = pd.DataFrame(columns=['username', 'bar', 'game', 'when', 'message', 'timestamp', 'reported'])
        
        new_row = pd.DataFrame([post])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    except:
        pass

def load_game_requests():
    if os.path.exists(GAME_REQUESTS_CSV_PATH):
        try:
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []

def save_game_request(request):
    try:
        if os.path.exists(GAME_REQUESTS_CSV_PATH):
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
        else:
            df = pd.DataFrame(columns=['timestamp', 'username', 'bar_name', 'game_name', 'action_type', 'description', 'status'])
        
        new_row = pd.DataFrame([request])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    except:
        pass

def approve_game_request(index):
    request = st.session_state.game_requests[index]
    new_row = pd.DataFrame({'bar_name': [request['bar_name']], 'game': [request['game_name']]})
    st.session_state.games_data = pd.concat([st.session_state.games_data, new_row], ignore_index=True)
    request['status'] = 'approved'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')

def reject_game_request(index):
    request = st.session_state.game_requests[index]
    request['status'] = 'rejected'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')

def delete_forum_post(index):
    st.session_state.forum_posts.pop(index)
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    except:
        pass

def report_forum_post(index):
    st.session_state.forum_posts[index]['reported'] = True
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    except:
        pass

# Load data at startup
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()

if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()

if len(st.session_state.game_requests) == 0:
    st.session_state.game_requests = load_game_requests()

# Discreet Admin Button (small emoji)
st.markdown("""<style>
.admin-btn {position: fixed; top: 70px; right: 20px; z-index: 999;}
.admin-btn button {font-size: 16px !important; padding: 5px 10px !important;}
</style>""", unsafe_allow_html=True)

col_header1, col_header2 = st.columns([20, 1])
with col_header2:
    if st.button("�"):
        st.session_state.show_admin_panel = not st.session_state.show_admin_panel

# Admin Panel
if st.session_state.show_admin_panel:
    st.markdown("---")
    st.markdown("### 🔐 Accès Administrateur")
    if not st.session_state.admin_logged_in:
        admin_pw = st.text_input("Mot de passe:", type="password", key="admin_login")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Se connecter"):
                if admin_pw == "admin123":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect")
        with col2:
            if st.button("Annuler"):
                st.session_state.show_admin_panel = False
                st.rerun()
    else:
        st.success("✅ Connecté")
        if st.button("Se déconnecter"):
            st.session_state.admin_logged_in = False
            st.session_state.show_admin_panel = False
            st.rerun()
    st.markdown("---")

# Header
st.title("🎮 Recherche de Bars à Jeux à Paris")
st.markdown("*Trouvez votre prochaine destination de jeu et connectez-vous avec d'autres joueurs !*")
st.markdown("---")

# Optimized: cache geodata loading
@st.cache_data
def load_data():
    gdf_bar = gpd.read_file("liste_bar_OK.geojson")
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # Main tabs (Admin only shows when logged in)
    if st.session_state.admin_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "🎮 Liste des Jeux", "💬 Forum", "🔧 Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["🗺️ Carte", "🎮 Liste des Jeux", "💬 Forum"])
    
    # TAB 1: Map and Search
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("🔍 Trouver un Bar")
            
            # Alphabetical bar menu instead of search
            bar_options = ["Tous les Bars"] + sorted(gdf_bar['Nom'].tolist())
            selected_bar = st.selectbox("Sélectionner un bar :", bar_options)
            
            # Arrondissement filter
            arrondissements = sorted(gdf_bar['Arrondissement'].dropna().unique(), key=lambda x: int(x) if str(x).isdigit() else 999)
            selected_arrond = st.selectbox("Arrondissement :", ["Tous"] + [str(a) for a in arrondissements])
            
            # Game filter
            if not st.session_state.games_data.empty:
                all_games = sorted(st.session_state.games_data['game'].unique())
                selected_game = st.selectbox("Jeu :", ["Tous les Jeux"] + all_games)
            else:
                selected_game = "Tous les Jeux"
            
            # Apply filters
            filtered_gdf = gdf_bar.copy()
            has_filter = False
            
            if selected_bar != "Tous les Bars":
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'] == selected_bar]
                has_filter = True
            
            if selected_arrond != "Tous":
                filtered_gdf = filtered_gdf[filtered_gdf['Arrondissement'].astype(str) == selected_arrond]
                has_filter = True
            
            if selected_game != "Tous les Jeux":
                bars_with_game = st.session_state.games_data[st.session_state.games_data['game'] == selected_game]['bar_name'].unique()
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].isin(bars_with_game)]
                has_filter = True
            
            # Show bar list only when filtered
            if has_filter and len(filtered_gdf) > 0:
                st.info(f"{len(filtered_gdf)} bar(s)")
                st.markdown("---")
                for idx, row in filtered_gdf.iterrows():
                    bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                    game_count = len(bar_games)
                    
                    st.markdown(f"""<div style='background-color: #E6F3FF; padding: 12px; border-radius: 8px; margin-bottom: 10px;'>
                    <h4 style='margin:0; color: #0066CC;'>📍 {row['Nom']}</h4>
                    </div>""", unsafe_allow_html=True)
                    
                    if pd.notna(row['Adresse']):
                        st.write(f"**Adresse:** {row['Adresse']}")
                    if pd.notna(row['Arrondissement']):
                        st.write(f"**Arrondissement:** {row['Arrondissement']}")
                    if pd.notna(row['Métro']):
                        st.write(f"**Métro:** {row['Métro']}")
                    if pd.notna(row['Téléphone']):
                        st.write(f"**Tél:** {row['Téléphone']}")
                    if pd.notna(row['Site']):
                        st.write(f"**Site:** {row['Site']}")
                    if game_count > 0:
                        st.write(f"**🎮 Jeux:** {game_count}")
                    st.markdown("---")
            elif has_filter:
                st.warning("Aucun bar trouvé")
        
        with col1:
            st.subheader("🗺️ Carte")
            if has_filter and len(filtered_gdf) > 0:
                st.map(filtered_gdf[['lat', 'lon']])
            else:
                st.map(gdf_bar[['lat', 'lon']])
    
    # TAB 2: Game List
    with tab2:
        st.subheader("🎮 Liste des Jeux")
        
        col1, col2 = st.columns(2)
        with col1:
            search_bar_filter = st.selectbox("Bar :", ["Tous"] + sorted(gdf_bar['Nom'].tolist()), key="game_bar")
        with col2:
            search_game_text = st.text_input("Rechercher jeu :", placeholder="Nom du jeu...")
        
        filtered_games = st.session_state.games_data.copy()
        
        if search_bar_filter != "Tous":
            filtered_games = filtered_games[filtered_games['bar_name'] == search_bar_filter]
        
        if search_game_text:
            filtered_games = filtered_games[filtered_games['game'].str.contains(search_game_text, case=False, na=False)]
        
        if not filtered_games.empty:
            st.markdown(f"**{len(filtered_games)} jeu(x)**")
            st.markdown("---")
            
            # Use details/summary HTML for clean compartmentalization
            for bar in filtered_games['bar_name'].unique():
                games = sorted(filtered_games[filtered_games['bar_name'] == bar]['game'].tolist())
                
                with st.expander(f"📍 {bar} ({len(games)} jeux)", expanded=False):
                    cols_per_row = 3
                    for i in range(0, len(games), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, game in enumerate(games[i:i+cols_per_row]):
                            cols[j].write(f"🎮 {game}")
        else:
            st.info("Aucun jeu")
        
        st.markdown("---")
        st.markdown("### ➕ Demander un Jeu")
        with st.form("request_game"):
            col1, col2 = st.columns(2)
            with col1:
                req_user = st.text_input("Nom :")
                req_bar = st.selectbox("Bar :", gdf_bar['Nom'].sort_values().tolist())
            with col2:
                req_game = st.text_input("Jeu :")
                req_action = st.selectbox("Type :", ["Ajouter", "Modifier"])
            req_desc = st.text_area("Description :")
            
            if st.form_submit_button("📤 Envoyer"):
                if req_user and req_game and req_bar:
                    request = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'username': req_user,
                        'bar_name': req_bar,
                        'game_name': req_game,
                        'action_type': req_action.lower(),
                        'description': req_desc,
                        'status': 'pending'
                    }
                    st.session_state.game_requests.append(request)
                    save_game_request(request)
                    st.success("✅ Envoyé")
                else:
                    st.error("⚠️ Champs requis manquants")
    
    # TAB 3: Forum
    with tab3:
        st.subheader("💬 Forum")
        
        with st.form("new_post"):
            username = st.text_input("Nom :")
            bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
            
            game_type = st.radio("Comment entrer le jeu ?", ["Taper le nom", "Sélectionner"], horizontal=True)
            
            if game_type == "Taper le nom":
                game_choice = st.text_input("Nom du jeu :", placeholder="Tapez le nom du jeu")
            else:
                if not st.session_state.games_data.empty:
                    game_choice = st.selectbox("Sélectionner un jeu :", ["N'importe quel Jeu"] + sorted(st.session_state.games_data['game'].unique()))
                else:
                    game_choice = st.text_input("Jeu :", placeholder="Aucun jeu disponible, tapez le nom")
            
            date_time = st.text_input("Quand :", placeholder="ex: Demain 19h")
            message = st.text_area("Message :")
            
            if st.form_submit_button("📤 Publier"):
                if username and message and game_choice:
                    post = {
                        'username': username,
                        'bar': bar_choice,
                        'game': game_choice,
                        'when': date_time,
                        'message': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'reported': False
                    }
                    st.session_state.forum_posts.insert(0, post)
                    save_forum_comment(post)
                    st.success("✅ Posté")
                    st.rerun()
                else:
                    st.error("Remplissez tous les champs")
        
        st.markdown("---")
        st.markdown("**Posts Récents**")
        
        if len(st.session_state.forum_posts) == 0:
            st.info("Aucun post")
        else:
            for idx, post in enumerate(st.session_state.forum_posts):
                col1, col2 = st.columns([4, 1])
                with col1:
                    reported_flag = "🚩 " if post.get('reported', False) else ""
                    st.markdown(f"{reported_flag}**{post['username']}** • {post['timestamp']}")
                    st.markdown(f"🎮 {post['game']} @ 📍 {post['bar']}")
                    if post.get('when'):
                        st.markdown(f"🕐 {post['when']}")
                    st.markdown(f"{post['message']}")
                with col2:
                    if not post.get('reported', False):
                        if st.button("🚩", key=f"report_{idx}"):
                            report_forum_post(idx)
                            st.rerun()
                st.markdown("---")
    
    # TAB 4: Admin (only if logged in)
    if st.session_state.admin_logged_in:
        with tab4:
            st.subheader("🔧 Administration")
            
            # Game Requests
            st.markdown("### Requêtes de Jeux")
            status_filter = st.selectbox("Statut :", ["Tous", "En attente", "Approuvé", "Rejeté"])
            
            filtered_reqs = st.session_state.game_requests.copy()
            if status_filter == "En attente":
                filtered_reqs = [r for r in filtered_reqs if r['status'] == 'pending']
            elif status_filter == "Approuvé":
                filtered_reqs = [r for r in filtered_reqs if r['status'] == 'approved']
            elif status_filter == "Rejeté":
                filtered_reqs = [r for r in filtered_reqs if r['status'] == 'rejected']
            
            st.write(f"**{len(filtered_reqs)} requête(s)**")
            
            for idx, req in enumerate(filtered_reqs):
                real_idx = st.session_state.game_requests.index(req)
                
                status_icon = "🔵" if req['status'] == 'pending' else "✅" if req['status'] == 'approved' else "❌"
                st.markdown(f"""<div style='background-color: #E6F3FF; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                <strong>{status_icon} {req['game_name']} @ {req['bar_name']}</strong>
                </div>""", unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Date:** {req['timestamp']}")
                    st.write(f"**User:** {req['username']}")
                    if req['description']:
                        st.write(f"**Desc:** {req['description']}")
                with col2:
                    if req['status'] == 'pending':
                        if st.button("✅", key=f"app_{real_idx}"):
                            approve_game_request(real_idx)
                            st.rerun()
                        if st.button("❌", key=f"rej_{real_idx}"):
                            reject_game_request(real_idx)
                            st.rerun()
                st.markdown("---")
            
            # Forum Moderation
            st.markdown("### Modération Forum")
            reported_posts = [i for i, p in enumerate(st.session_state.forum_posts) if p.get('reported', False)]
            
            if reported_posts:
                st.warning(f"🚩 {len(reported_posts)} post(s) signalé(s)")
                for idx in reported_posts:
                    post = st.session_state.forum_posts[idx]
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{post['username']}** • {post['timestamp']}")
                        st.markdown(f"{post['message']}")
                    with col2:
                        if st.button("🗑️", key=f"del_{idx}"):
                            delete_forum_post(idx)
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Aucun post signalé")

except FileNotFoundError:
    st.error("⚠️ Fichier introuvable")
except Exception as e:
    st.error(f"⚠️ Erreur: {str(e)}")

st.markdown("---")
st.markdown("*Créé par Kalma et José bestie :)*")
