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
import json
import folium
from streamlit_folium import st_folium
import hashlib
import glob

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
    
    /* Horizontal reactions on mobile */
    .reaction-container {
        display: flex;
        flex-direction: row;
        gap: 5px;
        flex-wrap: wrap;
        margin-top: 5px;
    }
    .reaction-btn {
        background: none !important;
        border: none !important;
        padding: 0 5px !important;
        cursor: pointer;
        font-size: 18px !important; /* Slightly larger emoji for visibility */
        line-height: 1.2;
    }
    .reaction-btn:hover {transform: scale(1.2);}
    
    /* Comment styling */
    .comment-box {
        background-color: #f8f9fa;
        border-left: 3px solid #1E90FF;
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 0 8px 8px 0;
    }
    .comment-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 0.9em;
        color: #666;
    }
    .comment-author {
        font-weight: bold;
        color: #0066CC;
    }
</style>
""", unsafe_allow_html=True)
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'show_admin_panel' not in st.session_state:
    st.session_state.show_admin_panel = False
if 'show_games' not in st.session_state:
    st.session_state.show_games = {}
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = []
if 'game_requests' not in st.session_state:
    st.session_state.game_requests = []
if 'games_data' not in st.session_state:
    st.session_state.games_data = pd.DataFrame()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_icon' not in st.session_state:
    st.session_state.user_icon = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"

# File paths
USERS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'users.json')
FORUM_CSV_PATH = os.path.join(os.path.dirname(__file__), 'forum_comments.csv')
GAME_REQUESTS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'game_requests.csv')
ICONS_DIR = os.path.join(os.path.dirname(__file__), 'icone_joueurs', 'icone_joueurs')

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
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if git is initialized
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        st.error("⚠️ Git n'est pas initialisé dans ce dossier.")
        return

    try:
        # Add files
        result_add = subprocess.run(['git', 'add', 'forum_comments.csv', 'game_requests.csv'], 
                                  cwd=repo_dir, 
                                  capture_output=True, 
                                  text=True)
        
        if result_add.returncode != 0:
            st.error(f"Git Add Error: {result_add.stderr}")
            return
            
        # Commit changes
        result_commit = subprocess.run(['git', 'commit', '-m', 'Auto-update CSV files'], 
                                     cwd=repo_dir, 
                                     capture_output=True, 
                                     text=True)
        
        if result_commit.returncode != 0:
            if "nothing to commit" in result_commit.stdout.lower():
                pass # No changes
            else:
                st.error(f"Git Commit Error: {result_commit.stderr}")
        else:
            st.toast("✅ Sauvegardé et commité !", icon="💾")
            
    except FileNotFoundError:
        st.error("⚠️ Git n'est pas installé ou n'est pas dans le PATH.")
    except Exception as e:
        st.error(f"Auto-commit failed: {str(e)}")

# --- User Management Functions ---
def load_users():
    if os.path.exists(USERS_JSON_PATH):
        try:
            with open(USERS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users_list):
    with open(USERS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, indent=4, ensure_ascii=False)
    
    # Auto-commit users.json
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run(['git', 'add', 'users.json'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Update users'], cwd=repo_dir, capture_output=True)
    except:
        pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, icon_path):
    users = load_users()
    if any(u['username'] == username for u in users):
        return False, "Ce nom d'utilisateur existe déjà."
    
    new_user = {
        'username': username,
        'password': hash_password(password),
        'icon': icon_path,
        'role': 'user' # Default role
    }
    users.append(new_user)
    save_users(users)
    return True, "Compte créé avec succès !"

def verify_user(username, password):
    users = load_users()
    
    # Check for hardcoded admin first if not in DB (or migration)
    if username == "admin" and password == "admin123":
        # Ensure admin exists in DB
        if not any(u['username'] == 'admin' for u in users):
            admin_user = {
                'username': 'admin',
                'password': hash_password('admin123'),
                'icon': '',
                'role': 'admin'
            }
            users.append(admin_user)
            save_users(users)
        return True, {'username': 'admin', 'role': 'admin', 'icon': ''}

    encoded_pw = hash_password(password)
    for user in users:
        if user['username'] == username and user['password'] == encoded_pw:
            return True, user
    return False, None

def get_available_icons():
    if os.path.exists(ICONS_DIR):
        # List png files
        return glob.glob(os.path.join(ICONS_DIR, "*.png"))
    return []

# --- Login / Register Page ---
def login_page():
    st.markdown("<h1 style='text-align: center; color: #003366;'>🏰 Echec et Map - Connexion</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Se connecter", "📝 Créer un compte"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", type="primary")
            
            if submit:
                success, user_data = verify_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data['username']
                    st.session_state.role = user_data.get('role', 'user')
                    st.session_state.user_icon = user_data.get('icon', '')
                    if st.session_state.role == 'admin':
                        st.session_state.admin_logged_in = True
                        st.session_state.show_admin_panel = True
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")

    with tab2:
        st.markdown("### Choisissez votre avatar")
        icons = get_available_icons()
        selected_icon = None
        
        # Display icons in a grid for selection
        if icons:
            # We use a selectbox for simplicity but show images below
            # Or better: use radio with custom formatting or just clickable images?
            # Streamlit doesn't support clickable images easily without component.
            # We will use st.image and a selectbox for the confirmation.
            
            # Let's map indices to filenames for easier selection
            icon_options = {os.path.basename(p): p for p in icons}
            
            # Show icons in grid
            cols = st.columns(6)
            for i, icon_path in enumerate(icons):
                with cols[i % 6]:
                    st.image(icon_path, use_column_width=True)
                    st.caption(f"Icone {i+1}")
            
            selected_icon_name = st.selectbox("Choisissez votre icone :", list(icon_options.keys()), format_func=lambda x: x)
            selected_icon = icon_options[selected_icon_name]
        
        with st.form("register_form"):
            new_user = st.text_input("Choisir un nom d'utilisateur")
            new_pass = st.text_input("Choisir un mot de passe", type="password")
            confirm_pass = st.text_input("Confirmer le mot de passe", type="password")
            
            reg_submit = st.form_submit_button("Créer mon compte")
            
            if reg_submit:
                if new_pass != confirm_pass:
                    st.error("Les mots de passe ne correspondent pas.")
                elif not new_user or not new_pass:
                    st.error("Veuillez remplir tous les champs.")
                elif not selected_icon:
                    st.error("Veuillez choisir une icône (vérifiez que le dossier icone_joueurs contient des images).")
                else:
                    success, msg = create_user(new_user, new_pass, selected_icon)
                    if success:
                        st.success(msg)
                        st.info("Vous pouvez maintenant vous connecter dans l'onglet 'Se connecter'.")
                    else:
                        st.error(msg)

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

def load_game_requests():
    if os.path.exists(GAME_REQUESTS_CSV_PATH):
        try:
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []

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

def save_forum_comment(comment):
    """Save a forum comment to CSV and auto-commit"""
    df = pd.DataFrame(st.session_state.forum_posts)
    df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()

def save_game_request(request):
    """Save a game request to CSV and auto-commit"""
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()

    return []

def add_reaction(post_idx, emoji):
    """Add a reaction to a post"""
    if 'reactions' not in st.session_state.forum_posts[post_idx]:
        st.session_state.forum_posts[post_idx]['reactions'] = {}
    
    reactions = st.session_state.forum_posts[post_idx]['reactions']
    if isinstance(reactions, str):
        try:
            reactions = json.loads(reactions)
        except:
            reactions = {}
    
    reactions[emoji] = reactions.get(emoji, 0) + 1
    st.session_state.forum_posts[post_idx]['reactions'] = json.dumps(reactions, ensure_ascii=False)
    save_forum_comment(None)

def add_comment_to_post(post_idx, author, text):
    """Add a comment to a post"""
    comment = {
        'author': author,
        'text': text,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if 'comments' not in st.session_state.forum_posts[post_idx]:
        st.session_state.forum_posts[post_idx]['comments'] = []
    
    comments = st.session_state.forum_posts[post_idx]['comments']
    if isinstance(comments, str):
        try:
            comments = json.loads(comments)
        except:
            comments = []
    
    comments.append(comment)
    st.session_state.forum_posts[post_idx]['comments'] = json.dumps(comments, ensure_ascii=False)
    save_forum_comment(None)

def delete_comment(post_idx, comment_idx):
    """Delete a comment from a post"""
    comments = st.session_state.forum_posts[post_idx].get('comments', [])
    if isinstance(comments, str):
        try:
            comments = json.loads(comments)
        except:
            comments = []
    
    if 0 <= comment_idx < len(comments):
        comments.pop(comment_idx)
        st.session_state.forum_posts[post_idx]['comments'] = json.dumps(comments, ensure_ascii=False)
        save_forum_comment(None)

def delete_forum_post(post_idx):
    """Delete a forum post"""
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts.pop(post_idx)
        save_forum_comment(None)

def report_forum_post(post_idx, reason):
    """Report a forum post"""
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts[post_idx]['reported'] = True
        st.session_state.forum_posts[post_idx]['report_reason'] = reason
        save_forum_comment(None)

def approve_game_request(req_idx):
    """Approve a game request"""
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'approved'
        save_game_request(None)

def reject_game_request(req_idx):
    """Reject a game request"""
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'rejected'
        save_game_request(None)


# Load data
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()
    # Parse JSON comments on load
    for post in st.session_state.forum_posts:
        if 'comments' in post and isinstance(post['comments'], str):
            try:
                post['comments'] = json.loads(post['comments'])
            except:
                # Handle legacy
                if '|||' in post['comments']:
                    legacy = post['comments'].split('|||')
                    post['comments'] = [{'author': 'Anonyme', 'text': c, 'timestamp': ''} for c in legacy if c]
                else:
                    post['comments'] = []

if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()
if len(st.session_state.game_requests) == 0:
    st.session_state.game_requests = load_game_requests()

col_header1, col_header2 = st.columns([20, 1])
with col_header2:
    if st.button("🔧"):
        st.session_state.show_admin_panel = not st.session_state.show_admin_panel

# Admin Panel - display in full width when activated
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
st.title("🎮 Echec et Map")
st.markdown("*Une application pour les amateurs de jeux de sociétés !*")

if st.session_state.logged_in:
    col_logout = st.columns([1])[0] # Just to put it somewhere or in sidebar
    with st.sidebar:
        st.write(f"Bienvenue, **{st.session_state.username}** !")
        if st.session_state.user_icon and os.path.exists(st.session_state.user_icon):
            st.image(st.session_state.user_icon, width=100)
        
        if st.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = "user"
            st.session_state.admin_logged_in = False
            st.rerun()
else:
    login_page()
    st.stop() # Stop execution here so the rest of the app doesn't run

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
    
    # TAB 1: Map (Folium)
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
            st.subheader("🗺️ Carte Interactive")
            
            # Map point selection
            if has_filter and len(filtered_gdf) > 0:
                map_data = filtered_gdf
            else:
                map_data = gdf_bar
            
            # Center map
            center_lat = map_data['lat'].mean()
            center_lon = map_data['lon'].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB dark_matter")
            
            for idx, row in map_data.iterrows():
                bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                game_count = len(bar_games)
                
                popup_html = f"""
                <div style="font-family: 'Corbel', sans-serif; min-width: 200px;">
                    <h4 style="color: #1E90FF; margin-bottom: 5px;">{row['Nom']}</h4>
                    <p style="margin: 2px 0;"><b>Adresse:</b> {row['Adresse']}</p>
                    <p style="margin: 2px 0;"><b>Jeux:</b> {game_count}</p>
                </div>
                """
                
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['Nom'],
                    icon=folium.Icon(color="blue", icon="glass", prefix="fa")
                ).add_to(m)
            
            # Capture map interactions
            map_output = st_folium(m, width="100%", height=600, key="folium_map")
            
            # Update filter based on marker click
            if map_output and map_output.get("last_object_clicked"):
                clicked_lat = map_output["last_object_clicked"].get("lat")
                clicked_lng = map_output["last_object_clicked"].get("lng")
                
                if clicked_lat and clicked_lng:
                    # Find the bar that was clicked
                    for idx, row in map_data.iterrows():
                        if abs(row['lat'] - clicked_lat) < 0.0001 and abs(row['lon'] - clicked_lng) < 0.0001:
                            # Update the displayed info to show only this bar
                            filtered_gdf = map_data[map_data['Nom'] == row['Nom']]
                            has_filter = True
                            break

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
            # Username is now automatic
            st.write(f"**Auteur :** {st.session_state.username}")
            bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
            game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
            date_time = st.text_input("Quand :", placeholder="ex: Demain 19h")
            message = st.text_area("Message :")
            
            if st.form_submit_button("Publier"):
                if message and game_choice:
                    post = {
                        'username': st.session_state.username,
                        'user_icon': st.session_state.user_icon, # Store icon path with post
                        'bar': bar_choice,
                        'game': game_choice,
                        'when': date_time,
                        'message': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'reported': False,
                        'report_reason': '',
                        'reactions': '',
                        'comments': [] # Initialize as empty list
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
                    
                    # Display icon if available
                    auth_icon = post.get('user_icon', '')
                    icon_html = ""
                    if auth_icon and os.path.exists(auth_icon):
                         # Convert local path to something we can display? 
                         # Streamlit usually needs a direct image call or base64 for HTML. 
                         # For simplicity in Markdown/HTML, we might struggle with local paths in 'st.markdown'.
                         # Let's use columns for the icon.
                         pass
                    
                    # Header with icon
                    col_icon, col_info = st.columns([1, 10])
                    with col_icon:
                         if auth_icon and os.path.exists(auth_icon):
                             st.image(auth_icon, width=40)
                         else:
                             st.write("👤")
                    with col_info:
                        st.markdown(f"{reported_flag}**{post['username']}** • {post['timestamp']}")
                        st.markdown(f"🎮 {post['game']} @ 📍 {post['bar']}")
                    
                    if post.get('when'):
                        st.markdown(f"🕐 {post['when']}")
                    st.markdown(f"{post['message']}")
                    
                    # Reactions (Horizontal Layout)
                    reactions = post.get('reactions', '')
                    if reactions:
                        # Parse and display reactions properly
                        if isinstance(reactions, str):
                            try:
                                reactions_dict = json.loads(reactions)
                                reaction_display = ' '.join([f"{emoji} {count}" for emoji, count in reactions_dict.items()])
                                st.markdown(f"**Réactions:** {reaction_display}")
                            except:
                                st.markdown(f"**Réactions:** {reactions}")
                        else:
                            st.markdown(f"**Réactions:** {reactions}")
                    
                    # Custom HTML for horizontal reaction buttons
                    st.markdown('<div class="reaction-container">', unsafe_allow_html=True)
                    cols = st.columns([1,1,1,1,6]) # Force small columns for buttons
                    with cols[0]:
                        if st.button("👍", key=f"like_{idx}"):
                            add_reaction(idx, "👍")
                            st.rerun()
                    with cols[1]:
                        if st.button("❤️", key=f"love_{idx}"):
                            add_reaction(idx, "❤️")
                            st.rerun()
                    with cols[2]:
                        if st.button("😂", key=f"laugh_{idx}"):
                            add_reaction(idx, "😂")
                            st.rerun()
                    with cols[3]:
                        if st.button("🎮", key=f"game_{idx}"):
                            add_reaction(idx, "🎮")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Comments
                    comments = post.get('comments', [])
                    if isinstance(comments, str): # Handle legacy
                        try:
                            comments = json.loads(comments)
                        except:
                            comments = []
                            
                    if comments:
                        st.markdown("**Commentaires:**")
                        for c_idx, comment in enumerate(comments):
                            # Professional comment layout
                            st.markdown(f"""
                            <div class="comment-box">
                                <div class="comment-header">
                                    <span class="comment-author">{comment.get('author', 'Anonyme')}</span>
                                    <span>{comment.get('timestamp', '')}</span>
                                </div>
                                <div class="comment-text">{comment.get('text', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Delete comment button
                            if st.button("🗑️", key=f"del_com_{idx}_{c_idx}"):
                                delete_comment(idx, c_idx)
                                st.rerun()
                    
                    # Add comment
                    with st.form(f"comment_{idx}"):
                        col_c1, col_c2 = st.columns([1, 3])
                        with col_c1:
                            st.write(f"👤 {st.session_state.username}")
                        with col_c2:
                            c_text = st.text_input("Commentaire:", key=f"c_text_{idx}")
                            
                        if st.form_submit_button("💬 Commenter"):
                            if c_text:
                                add_comment_to_post(idx, st.session_state.username, c_text)
                                st.rerun()
                            else:
                                st.error("Message requis")
                
                with col2:
                    # Post deletion
                    if st.button("🗑️", key=f"del_post_{idx}", help="Supprimer mon post"):
                        delete_forum_post(idx)
                        st.success("Supprimé")
                        st.rerun()
                        
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
st.markdown("*Propriété d'Echec et Map*")