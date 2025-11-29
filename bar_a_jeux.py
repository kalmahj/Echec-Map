# -*- coding: utf-8 -*-
"""
Recherche de Bars à Jeux à Paris
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime
import os
import chardet
import subprocess

# Page config
st.set_page_config(page_title="Echec et Map", page_icon="🎮", layout="wide")

# CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@700&family=Montserrat:wght@600&family=Open+Sans&display=swap');
    
    h1 {font-family: 'Rockwell', 'Castellar', 'Roboto Slab', serif !important; color: #003366 !important;}
    h2, h3 {font-family: 'Eras Demi ITC', 'Montserrat', sans-serif !important; color: #0066CC !important;}
    p, div, span, label, input, textarea, select {font-family: 'Corbel', 'Open Sans', sans-serif !important;}
    
    .stButton>button {background-color: #1E90FF !important; color: white !important; border-radius: 8px !important;}
    .stButton>button:hover {background-color: #0066CC !important;}
    
    .stTabs [data-baseweb="tab"] {background-color: #E6F3FF; border-radius: 8px 8px 0 0;}
    .stTabs [aria-selected="true"] {background-color: #1E90FF !important; color: white !important;}
    
    .bar-box {background: #E6F3FF; padding: 10px; border-radius: 8px; margin: 5px 0; cursor: pointer; border: 1px solid #1E90FF;}
    .bar-box:hover {background: #D0E8FF;}
    .game-item {padding: 5px; margin: 3px 0;}
    .reaction-btn {font-size: 20px; cursor: pointer; margin: 0 5px;}
</style>
""", unsafe_allow_html=True)

# Session state
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
if 'selected_map_bar' not in st.session_state:
    st.session_state.selected_map_bar = None
if 'show_games' not in st.session_state:
    st.session_state.show_games = {}

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

# Auto-commit CSV function
def auto_commit_csv():
    try:
        # Add files
        result_add = subprocess.run(['git', 'add', FORUM_CSV_PATH, GAME_REQUESTS_CSV_PATH], 
                                  cwd=os.path.dirname(__file__), 
                                  capture_output=True, 
                                  text=True)
        if result_add.returncode != 0:
            st.error(f"Git Add Error: {result_add.stderr}")
            print(f"Git Add Error: {result_add.stderr}")
            
        # Commit changes
        result_commit = subprocess.run(['git', 'commit', '-m', 'Auto-update CSV files'], 
                                     cwd=os.path.dirname(__file__), 
                                     capture_output=True, 
                                     text=True)
        
        if result_commit.returncode != 0:
            # Ignore "nothing to commit" errors
            if "nothing to commit" not in result_commit.stdout:
                st.error(f"Git Commit Error: {result_commit.stderr}")
                print(f"Git Commit Error: {result_commit.stderr}")
            else:
                print("Nothing to commit")
        else:
            st.toast("✅ Sauvegardé et commité !", icon="💾")
            print("Auto-commit successful")
            
    except Exception as e:
        st.error(f"Auto-commit failed: {str(e)}")
        print(f"Auto-commit exception: {str(e)}")

@st.cache_data
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

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
            df = pd.DataFrame(columns=['username', 'bar', 'game', 'when', 'message', 'timestamp', 'reported', 'report_reason', 'reactions', 'comments'])
        
        new_row = pd.DataFrame([post])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
        auto_commit_csv()
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
        auto_commit_csv()
    except:
        pass

def approve_game_request(index):
    request = st.session_state.game_requests[index]
    new_row = pd.DataFrame({'bar_name': [request['bar_name']], 'game': [request['game_name']]})
    st.session_state.games_data = pd.concat([st.session_state.games_data, new_row], ignore_index=True)
    request['status'] = 'approved'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()

def reject_game_request(index):
    request = st.session_state.game_requests[index]
    request['status'] = 'rejected'
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()

def delete_forum_post(index):
    st.session_state.forum_posts.pop(index)
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
        auto_commit_csv()
    except:
        pass

def report_forum_post(index, reason):
    st.session_state.forum_posts[index]['reported'] = True
    st.session_state.forum_posts[index]['report_reason'] = reason
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
        auto_commit_csv()
    except:
        pass

def add_reaction(index, emoji):
    if 'reactions' not in st.session_state.forum_posts[index] or pd.isna(st.session_state.forum_posts[index]['reactions']):
        st.session_state.forum_posts[index]['reactions'] = emoji
    else:
        st.session_state.forum_posts[index]['reactions'] += f",{emoji}"
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
        auto_commit_csv()
    except:
        pass

def add_comment_to_post(index, comment):
    if 'comments' not in st.session_state.forum_posts[index] or pd.isna(st.session_state.forum_posts[index]['comments']):
        st.session_state.forum_posts[index]['comments'] = comment
    else:
        st.session_state.forum_posts[index]['comments'] += f"|||{comment}"
    try:
        df = pd.DataFrame(st.session_state.forum_posts)
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
        auto_commit_csv()
    except:
        pass

# Load data
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()

if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()

if len(st.session_state.game_requests) == 0:
    st.session_state.game_requests = load_game_requests()

# Admin button
col_header1, col_header2 = st.columns([20, 1])
with col_header2:
    if st.button("🔧"):
        st.session_state.show_admin_panel = not st.session_state.show_admin_panel

if st.session_state.show_admin_panel:
    st.markdown("---")
    st.markdown("### 🔐 Accès Admin")
    if not st.session_state.admin_logged_in:
        admin_pw = st.text_input("Mot de passe:", type="password", key="admin_pw")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Connexion"):
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
        if st.button("Déconnexion"):
            st.session_state.admin_logged_in = False
            st.session_state.show_admin_panel = False
            st.rerun()
    st.markdown("---")

# Header
st.title("🎮 Echec et Map")
st.markdown("*Une application pour les amateurs de jeux de sociétés !*")
st.markdown("---")

@st.cache_data
def load_data():
    gdf_bar = gpd.read_file("liste_bar_OK.geojson")
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # Tabs
    if st.session_state.admin_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte", "🎮 Liste de jeux", "💬 Forum", "🔧 Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["🗺️ Carte", "🎮 Liste de jeux", "💬 Forum"])
    
    # TAB 1: Map
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("🔍 Recherche")
            
            bar_options = ["Tous"] + sorted(gdf_bar['Nom'].tolist())
            selected_bar = st.selectbox("Bar :", bar_options)
            
            arrondissements = sorted(gdf_bar['Arrondissement'].dropna().unique(), key=lambda x: int(x) if str(x).isdigit() else 999)
            selected_arrond = st.selectbox("Arrondissement :", ["Tous"] + [str(a) for a in arrondissements])
            
            if not st.session_state.games_data.empty:
                all_games = sorted(st.session_state.games_data['game'].unique())
                selected_game = st.selectbox("Jeu :", ["Tous"] + all_games)
            else:
                selected_game = "Tous"
            
            # Filters
            filtered_gdf = gdf_bar.copy()
            has_filter = False
            
            if selected_bar != "Tous":
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'] == selected_bar]
                has_filter = True
            
            if selected_arrond != "Tous":
                filtered_gdf = filtered_gdf[filtered_gdf['Arrondissement'].astype(str) == selected_arrond]
                has_filter = True
            
            if selected_game != "Tous":
                bars_with_game = st.session_state.games_data[st.session_state.games_data['game'] == selected_game]['bar_name'].unique()
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].isin(bars_with_game)]
                has_filter = True
            
            if has_filter and len(filtered_gdf) > 0:
                st.info(f"{len(filtered_gdf)} bar(s)")
                st.markdown("---")
                for idx, row in filtered_gdf.iterrows():
                    bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                    game_count = len(bar_games)
                    
                    st.markdown(f"""<div class='bar-box'><h4 style='margin:0; color: #0066CC;'>📍 {row['Nom']}</h4></div>""", unsafe_allow_html=True)
                    
                    if pd.notna(row['Adresse']):
                        st.write(f"**Adresse:** {row['Adresse']}")
                    if pd.notna(row['Arrondissement']):
                        st.write(f"**Arr:** {row['Arrondissement']}")
                    if pd.notna(row['Métro']):
                        st.write(f"**Métro:** {row['Métro']}")
                    if pd.notna(row['Téléphone']):
                        st.write(f"**Tél:** {row['Téléphone']}")
                    if game_count > 0:
                        st.write(f"**🎮:** {game_count}")
                    st.markdown("---")
            elif has_filter:
                st.warning("Aucun bar")
        
        with col1:
            st.subheader("🗺️ Carte")
            
            # Map point selection
            st.info("💡 Sélectionnez un bar dans le menu pour voir ses détails")
            
            if has_filter and len(filtered_gdf) > 0:
                st.map(filtered_gdf[['lat', 'lon']])
            else:
                st.map(gdf_bar[['lat', 'lon']])
    
    # TAB 2: Games
    with tab2:
        st.subheader("🎮 Liste des Jeux")
        
        col1, col2 = st.columns(2)
        with col1:
            search_bar_filter = st.selectbox("Bar :", ["Tous"] + sorted(gdf_bar['Nom'].tolist()), key="game_bar")
        with col2:
            search_game_text = st.text_input("Rechercher :", placeholder="Nom du jeu...")
        
        filtered_games = st.session_state.games_data.copy()
        
        if search_bar_filter != "Tous":
            filtered_games = filtered_games[filtered_games['bar_name'] == search_bar_filter]
        
        if search_game_text:
            filtered_games = filtered_games[filtered_games['game'].str.contains(search_game_text, case=False, na=False)]
        
        if not filtered_games.empty:
            st.markdown(f"**{len(filtered_games)} jeu(x)**")
            st.markdown("---")
            
            # Custom HTML compartmentalization
            for bar in filtered_games['bar_name'].unique():
                games = sorted(filtered_games[filtered_games['bar_name'] == bar]['game'].tolist())
                bar_id = bar.replace(" ", "_")
                
                if bar_id not in st.session_state.show_games:
                    st.session_state.show_games[bar_id] = False
                
                # Toggle button
                if st.button(f"{bar} ({len(games)} jeux)", key=f"toggle_{bar_id}"):
                    st.session_state.show_games[bar_id] = not st.session_state.show_games[bar_id]
                
                # Show games if toggled
                if st.session_state.show_games.get(bar_id, False):
                    cols_per_row = 3
                    for i in range(0, len(games), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, game in enumerate(games[i:i+cols_per_row]):
                            cols[j].markdown(f"<div class='game-item'>🎮 {game}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("Aucun jeu")
        
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
                    st.success("✅")
                else:
                    st.error("⚠️ Champs requis")
    
    # TAB 3: Forum
    with tab3:
        st.subheader("💬 Forum")
        
        with st.form("new_post"):
            username = st.text_input("Nom :")
            bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
            game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
            date_time = st.text_input("Quand :", placeholder="ex: Demain 19h")
            message = st.text_area("Message :")
            
            if st.form_submit_button("Publier"):
                if username and message and game_choice:
                    post = {
                        'username': username,
                        'bar': bar_choice,
                        'game': game_choice,
                        'when': date_time,
                        'message': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'reported': False,
                        'report_reason': '',
                        'reactions': '',
                        'comments': ''
                    }
                    st.session_state.forum_posts.insert(0, post)
                    save_forum_comment(post)
                    st.success("✅ Publié")
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
                    
                    # Reactions
                    reactions = post.get('reactions', '')
                    if reactions:
                        st.markdown(f"Réactions: {reactions}")
                    
                    # Add reaction
                    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
                    with col_r1:
                        if st.button("👍", key=f"like_{idx}"):
                            add_reaction(idx, "👍")
                            st.rerun()
                    with col_r2:
                        if st.button("❤️", key=f"love_{idx}"):
                            add_reaction(idx, "❤️")
                            st.rerun()
                    with col_r3:
                        if st.button("😂", key=f"laugh_{idx}"):
                            add_reaction(idx, "😂")
                            st.rerun()
                    with col_r4:
                        if st.button("🎮", key=f"game_{idx}"):
                            add_reaction(idx, "🎮")
                            st.rerun()
                    
                    # Comments
                    comments = post.get('comments', '')
                    if comments and comments != '':
                        st.markdown("**Commentaires:**")
                        for comment in comments.split('|||'):
                            if comment:
                                st.markdown(f"• {comment}")
                    
                    # Add comment
                    with st.form(f"comment_{idx}"):
                        new_comment = st.text_input("Ajouter un commentaire:", key=f"new_comment_{idx}")
                        if st.form_submit_button("💬"):
                            if new_comment:
                                add_comment_to_post(idx, new_comment)
                                st.rerun()
                
                with col2:
                    if not post.get('reported', False):
                        # Initialize report form state for this post if needed
                        if f"show_report_{idx}" not in st.session_state:
                            st.session_state[f"show_report_{idx}"] = False
                        
                        # Toggle button
                        if st.button("🚩 Signaler", key=f"toggle_report_{idx}"):
                            st.session_state[f"show_report_{idx}"] = not st.session_state[f"show_report_{idx}"]
                        
                        # Show form if toggled
                        if st.session_state[f"show_report_{idx}"]:
                            with st.form(f"report_form_{idx}"):
                                reason = st.text_input("Raison :")
                                if st.form_submit_button("Envoyer"):
                                    report_forum_post(idx, reason)
                                    st.session_state[f"show_report_{idx}"] = False # Close form
                                    st.success("Signalé à l'admin")
                                    st.rerun()
                
                st.markdown("---")
    
    # TAB 4: Admin
    if st.session_state.admin_logged_in:
        with tab4:
            st.subheader("🔧 Administration")
            
            st.markdown("### 📋 Requêtes d'ajout/modification")
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
                st.markdown(f"""<div class='bar-box'><strong>{status_icon} {req['game_name']} @ {req['bar_name']}</strong><br>
                <small>Type: {req['action_type']}</small></div>""", unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Date:** {req['timestamp']}")
                    st.write(f"**User:** {req['username']}")
                    if req['description']:
                        st.write(f"**Desc:** {req['description']}")
                with col2:
                    if req['status'] == 'pending':
                        if st.button("✅ Approuver", key=f"app_{real_idx}"):
                            approve_game_request(real_idx)
                            st.success("Approuvé")
                            st.rerun()
                        if st.button("❌ Rejeter", key=f"rej_{real_idx}"):
                            reject_game_request(real_idx)
                            st.warning("Rejeté")
                            st.rerun()
                st.markdown("---")
            
            st.markdown("### 🚨 Signalements Forum")
            reported_posts = [i for i, p in enumerate(st.session_state.forum_posts) if p.get('reported', False)]
            
            if reported_posts:
                st.warning(f"{len(reported_posts)} post(s) signalé(s)")
                for idx in reported_posts:
                    post = st.session_state.forum_posts[idx]
                    st.markdown(f"""<div style='border: 1px solid red; padding: 10px; border-radius: 5px;'>
                    <strong>Auteur:</strong> {post['username']}<br>
                    <strong>Message:</strong> {post['message']}<br>
                    <strong>Raison du signalement:</strong> {post.get('report_reason', 'Non spécifiée')}
                    </div>""", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Supprimer le post", key=f"del_{idx}"):
                            delete_forum_post(idx)
                            st.success("Post supprimé")
                            st.rerun()
                    with col2:
                        if st.button("✅ Ignorer (Retirer signalement)", key=f"ignore_{idx}"):
                            # Just remove reported flag
                            st.session_state.forum_posts[idx]['reported'] = False
                            save_forum_comment(st.session_state.forum_posts[idx]) # Save state change
                            st.info("Signalement retiré")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Aucun signalement à traiter")

except FileNotFoundError:
    st.error("⚠️ Fichier introuvable")
except Exception as e:
    st.error(f"⚠️ Erreur: {str(e)}")

st.markdown("---")
st.markdown("*Créé par Kalma et José bestie :)*")
