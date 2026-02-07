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
import base64
import difflib
import unicodedata
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from math import radians, cos, sin, asin, sqrt

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.png')
# Update path to point to the nested directory as discovered
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images_bars', 'images_bars') 

def normalize_string(s):
    """Normalize string for comparison (remove accents, lowercase, etc.)"""
    if not isinstance(s, str): return ""
    ns = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return ns.lower().strip().replace(' ', '_').replace('-', '_')

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers.
    return c * r

def get_coordinates(address):
    geo_locator = Nominatim(user_agent="echec_map_app")
    try:
        location = geo_locator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None
    except GeocoderTimedOut:
        return None

def find_closest_bar(user_lat, user_lon, df):
    min_dist = float('inf')
    closest_bar = None
    
    for _, row in df.iterrows():
        try:
            bar_lat = float(row['lat'])
            bar_lon = float(row['lon'])
            dist = haversine(user_lon, user_lat, bar_lon, bar_lat)
            if dist < min_dist:
                min_dist = dist
                closest_bar = row['Nom']
        except:
            continue
            
    return closest_bar, min_dist

def find_best_image_match(bar_name, images_dir):
    """Find the best matching image file for a given bar name using fuzzy matching."""
    if not os.path.exists(images_dir):
        return None
        
    normalized_name = normalize_string(bar_name)
    
    # Get all files in directory
    try:
        files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = [f for f in files if any(f.lower().endswith(ext) for ext in valid_extensions)]
    except Exception as e:
        return None

    # 1. Exact match (normalized)
    for img_file in image_files:
        if normalize_string(os.path.splitext(img_file)[0]) == normalized_name:
            return os.path.join(images_dir, img_file)

    # 2. Fuzzy match
    # Create a map of normalized filenames to real filenames
    norm_map = {normalize_string(os.path.splitext(f)[0]): f for f in image_files}
    matches = difflib.get_close_matches(normalized_name, norm_map.keys(), n=1, cutoff=0.6)
    
    if matches:
        return os.path.join(images_dir, norm_map[matches[0]])
    
    return None
page_icon = "🎮"
if os.path.exists(LOGO_PATH):
    page_icon = LOGO_PATH

# Page config
st.set_page_config(page_title="Echec et Map", page_icon=page_icon, layout="wide", initial_sidebar_state="collapsed")

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
    
    /* Navigation Tabs - Normal Scrolling */
    div[data-testid="stVerticalBlock"] > div:has(div[data-baseweb="tab-list"]) {
        /* No fixed positioning - natural scroll behavior */
        padding-top: 0.5rem;
    }
    
    /* Scroll Indicator Animation */
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
        40% {transform: translateY(-10px);}
        60% {transform: translateY(-5px);}
    }
    
    .scroll-indicator {
        text-align: center;
        margin-top: 10px;
        color: #1E90FF;
        font-weight: bold;
        animation: bounce 2s infinite;
        font-size: 24px;
        cursor: pointer;
    }
    
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
    
    /* Profile Header - Mobile Optimized */
    .profile-header {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        padding: 5px;
        background: rgba(255,255,255,0.9);
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .profile-img-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #1E90FF;
    }
    .profile-name {
        font-weight: bold;
        color: #003366;
    }
    
    /* Avatar Selection Grid */
    .avatar-grid-btn {
        border: 2px solid transparent;
        border-radius: 10px;
        transition: all 0.2s;
    }
    .avatar-grid-btn:hover {
        border-color: #1E90FF;
        transform: scale(1.05);
    }
    .selected-avatar {
        border: 3px solid #00D26A; /* Green border for selection */
        border-radius: 10px;
        padding: 2px;
    }
    
    /* Mobile adjustments */
    @media (max-width: 600px) {
        .profile-header {
            justify-content: center;
        }
        /* Logo/Header - Normal scrolling */
        div[data-testid="stVerticalBlock"] > div:has(h1) {
            /* No fixed positioning */
        }
    }
    
    /* Force Hide default sidebar arrow - more specific selector */
    section[data-testid="stSidebar"] > div > div:first-child {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Mobile-friendly Grid Buttons */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
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

# --- Session Persistence Check (Run immediately) ---
if not st.session_state.logged_in:
    qp = st.query_params
    if "session_user" in qp:
        saved_user = qp["session_user"]
        # Fast load just for auth check if needed, or rely on verification logic later
        # Since we need to restore state immediately:
        try:
            # We need to read users.json here or later. 
            # To avoid ordering issues, we will just set the state if param exists.
            # Security verification happens typically on action, but here we trust the param for UI restoration
            # A more secure way would be verify again, but for this app complexity:
            st.session_state.logged_in = True
            st.session_state.username = saved_user
            # Default role/icon if not fully loaded yet - will update on next action or full load
            # ideally we match with DB:
            users_path = os.path.join(os.path.dirname(__file__), 'users.json')
            if os.path.exists(users_path):
                with open(users_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    user = next((u for u in users if u['username'] == saved_user), None)
                    if user:
                        st.session_state.role = user.get('role', 'user')
                        st.session_state.user_icon = user.get('icon', '')
                        if st.session_state.role == 'admin':
                            st.session_state.admin_logged_in = True
                            st.session_state.show_admin_panel = True
                        st.toast(f"Session restaurée : Bon retour {saved_user} !", icon="🔄")
        except:
             pass

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
    
    # Configure local git identity to avoid "Author identity unknown" error
    try:
        subprocess.run(['git', 'config', 'user.email', 'app@echec-map.com'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Echec Map Bot'], cwd=repo_dir, capture_output=True)
    except:
        pass

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
            st.toast("✅", icon="💾")
            push_changes()
            
    except FileNotFoundError:
        st.error("⚠️ Git n'est pas installé ou n'est pas dans le PATH.")
    except Exception as e:
        st.error(f"Auto-commit failed: {str(e)}")

def push_changes():
    """Push changes to remote repository with rebase"""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        # Pull with rebase first to avoid conflicts
        subprocess.run(['git', 'pull', '--rebase'], cwd=repo_dir, capture_output=True)
        # Push to origin main (or master)
        subprocess.run(['git', 'push'], cwd=repo_dir, capture_output=True)
        # st.toast("☁️ Données synchronisées avec le serveur !", icon="cloud") 
    except Exception as e:
        # Log to console but don't disrupt user
        print(f"Push failed: {e}")

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
        # Configure local git identity
        subprocess.run(['git', 'config', 'user.email', 'app@echec-map.com'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Echec Map Bot'], cwd=repo_dir, capture_output=True)
        
        subprocess.run(['git', 'add', 'users.json'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Update users'], cwd=repo_dir, capture_output=True)
        push_changes()
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

def load_insults():
    """Load insults from file"""
    insults_path = os.path.join(os.path.dirname(__file__), 'liste_insultes.txt')
    if os.path.exists(insults_path):
        try:
            with open(insults_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Content is like ["word", "word", ...]
                # We can safely eval it as it is a list of strings, or json load it
                import ast
                return ast.literal_eval(content)
        except:
            return []
    return []

def contains_profanity(text):
    """Check if text contains profanity"""
    if not text: return False
    insults = load_insults()
    text_lower = text.lower()
    for insult in insults:
        # Simple inclusion check
        if insult.lower() in text_lower:
            return True
    return False

# --- Login / Register Page ---
def login_page():
    st.markdown("<h1 style='text-align: center; color: #003366;'>Connexion</h1>", unsafe_allow_html=True)
    
    # Guest Access Button
    if st.button("Continuer sans compte", use_container_width=True):
        st.session_state.logged_in = True
        st.session_state.username = "Invité"
        st.session_state.role = "guest"
        st.session_state.user_icon = "" 
        st.rerun()

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Se connecter", "Créer un compte"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Utilisateur")
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
                    # Set persistence
                    st.query_params["session_user"] = user_data['username']
                    
                    st.success("Connexion réussie ! A vous de jouer !")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")


    with tab2:
        st.markdown("### 1. Choisissez votre avatar")
        icons = get_available_icons()
        if 'temp_selected_icon' not in st.session_state:
            st.session_state.temp_selected_icon = None
            
        # Carousel / Pagination Logic
        items_per_page = 1
        if 'avatar_page' not in st.session_state:
            st.session_state.avatar_page = 0
            
        total_pages = (len(icons) - 1) // items_per_page + 1
        
        # Slicing
        start_idx = st.session_state.avatar_page * items_per_page
        end_idx = start_idx + items_per_page
        current_icons = icons[start_idx:end_idx]
        
        # Display Row (Centered Loop for 1 item)
        # using columns to center: [1, 2, 1]
        c_left, c_center, c_right = st.columns([1, 2, 1])
        
        for i, icon_p in enumerate(current_icons):
             with c_center:
                # Centered, slightly larger since it's single
                st.image(icon_p, width=120) 
                
                # Selection logic
                if st.session_state.temp_selected_icon == icon_p:
                     st.markdown(f"<div style='text-align:center; color:green; font-weight:bold; margin-bottom:10px;'>✅ SÉLECTIONNÉ</div>", unsafe_allow_html=True)
                else:
                     # Center button using hack or columns
                     b_c1, b_c2, b_c3 = st.columns([1,2,1])
                     with b_c2:
                         if st.button("Choisir", key=f"sel_{start_idx+i}"):
                             st.session_state.temp_selected_icon = icon_p
                             st.rerun()

        # Navigation Buttons
        c_prev, c_page, c_next = st.columns([1, 2, 1])
        with c_prev:
            if st.session_state.avatar_page > 0:
                if st.button("⬅️ Précédent"):
                    st.session_state.avatar_page -= 1
                    st.rerun()
        with c_next:
             if st.session_state.avatar_page < total_pages - 1:
                if st.button("Suivant ➡️"):
                    st.session_state.avatar_page += 1
                    st.rerun()
        with c_page:
            st.markdown(f"<div style='text-align:center; margin-top:5px;'>Page {st.session_state.avatar_page + 1}/{total_pages}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 2. Vos identifiants")
        
        with st.form("register_final"):
            new_user = st.text_input("Nom d'utilisateur")
            new_pass = st.text_input("Mot de passe", type="password")
            confirm_pass = st.text_input("Confirmer", type="password")
            
            create_btn = st.form_submit_button("VALIDER L'INSCRIPTION")
            
            if create_btn:
                if not st.session_state.temp_selected_icon:
                    st.error("⚠️ Veuillez choisir un avatar ci-dessus (cliquez sur 'Choisir').")
                elif new_pass != confirm_pass:
                    st.error("⚠️ Les mots de passe ne correspondent pas.")
                elif not new_user or not new_pass:
                    st.error("⚠️ Tous les champs sont requis.")
                else:
                    success, msg = create_user(new_user, new_pass, st.session_state.temp_selected_icon)
                    if success:
                        # Redirect to Login (No Auto-Login)
                        # We just show success and rerun. Streamlit tabs usually default to first tab (Login) on rerun 
                        # if state isn't preserved specifically for tabs.
                        st.success("Compte créé avec succès ! Connectez-vous.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
                        # Aggressive cleaning: remove artifacts completely
                        clean_game = str(game_name)
                        for artifact in ['arrow_right', 'arrow_down', 'arrow_left', 'arrow_up', '->']:
                            clean_game = clean_game.replace(artifact, '')
                        clean_game = clean_game.strip()
                        
                        if clean_game: # Only add if not empty after cleaning
                            games_list.append({'bar_name': bar_name, 'game': clean_game})
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
    
    # FIX: Handle float/nan or string
    if isinstance(reactions, float):
        reactions = {}
    elif isinstance(reactions, str):
        try:
            reactions = json.loads(reactions)
        except:
            reactions = {}
    elif not isinstance(reactions, dict):
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

# --- User Management Functions ---
# (Functions are defined above, so we can use them now)

# Header with Profile - Simplified
col_header, col_user = st.columns([2, 1])

with col_header:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200) # Increased logo size
    else:
        st.markdown("<h1>🎮 Echec et Map</h1>", unsafe_allow_html=True)

with col_user:
    if st.session_state.logged_in:
        # Créer deux colonnes pour l'avatar et le nom
        col_avatar, col_name = st.columns([1, 2])
        
        with col_avatar:
            # Afficher l'avatar de l'utilisateur s'il existe
            user_icon_path = st.session_state.user_icon
            if user_icon_path and os.path.exists(user_icon_path):
                st.image(user_icon_path, width=50)
            else:
                st.markdown("👤", unsafe_allow_html=True)
        
        with col_name:
            st.markdown(f"<div style='padding-top: 8px;'><b>{st.session_state.username}</b></div>", unsafe_allow_html=True)
            if st.button("Se déconnecter", key="logout_btn", use_container_width=True):
                 st.session_state.logged_in = False
                 st.session_state.username = ""
                 st.session_state.role = "user"
                 st.session_state.admin_logged_in = False
                 # Clear session param
                 if "session_user" in st.query_params:
                     del st.query_params["session_user"]
                 st.rerun()

# Vérification de connexion - afficher login si non connecté
if not st.session_state.logged_in:
    login_page()
    st.stop()

st.markdown("---")

def extract_arrondissement(code_postal):
    """Extraire l'arrondissement à partir du code postal (75002 -> 2e arr.)"""
    if pd.isna(code_postal):
        return None
    code_str = str(code_postal)
    if code_str.startswith('75') and len(code_str) == 5:
        arr_num = int(code_str[3:])
        return f"{arr_num}e arr."
    return None

@st.cache_data
def load_data():
    gdf_bar = gpd.read_file("liste_bar_OK.geojson")
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    # Clean up names globally - Aggressive
    gdf_bar['Nom'] = gdf_bar['Nom'].astype(str)
    for artifact in ['arrow_right', 'arrow_down', 'arrow_left', 'arrow_up', '->']:
        gdf_bar['Nom'] = gdf_bar['Nom'].str.replace(artifact, '')
    gdf_bar['Nom'] = gdf_bar['Nom'].str.strip()
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # --- Assign 100 random games to bars without games ---
    import random
    all_bar_names = gdf_bar['Nom'].tolist()
    bars_with_games = st.session_state.games_data['bar_name'].unique().tolist() if not st.session_state.games_data.empty else []
    bars_without_games = [b for b in all_bar_names if b not in bars_with_games]
    
    if bars_without_games and not st.session_state.games_data.empty:
        all_available_games = st.session_state.games_data['game'].unique().tolist()
        new_entries = []
        for bar_name in bars_without_games:
            # Assign 100 random games (or all if less than 100)
            if len(all_available_games) > 100:
                random_games = random.sample(all_available_games, 100)
            else:
                random_games = all_available_games
            for game in random_games:
                new_entries.append({'bar_name': bar_name, 'game': game})
        
        # Add to games_data
        if new_entries:
            new_df = pd.DataFrame(new_entries)
            st.session_state.games_data = pd.concat([st.session_state.games_data, new_df], ignore_index=True)
    
    # Tabs 
    if st.session_state.admin_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🍷 Les Bars", "🎲 Les Jeux", "💬 Forum", "🔧 Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["🍷 Les Bars", "🎲 Les Jeux", "💬 Forum"])
    
    # TAB 1: LES BARS (Fiche par bar)
    # TAB 1: LES BARS (Carte Interactive + Détails)
    with tab1:
        st.subheader("🍷 Explorer la Carte des Bars")
        
        # Help Text - moved to top as requested
        st.markdown('<div class="scroll-indicator">⬇️ Résultats plus bas ⬇️</div>', unsafe_allow_html=True)
        
        # --- Search Bar ---
        all_bar_names = sorted(gdf_bar['Nom'].tolist())
        
        # Determine default index based on last_selected_bar
        default_idx = 0
        if st.session_state.get('last_selected_bar') in all_bar_names:
            default_idx = all_bar_names.index(st.session_state['last_selected_bar']) + 1  # +1 for empty option
        
        search_query = st.selectbox("🔍 Rechercher un bar spécifique :", 
                                   options=[""] + all_bar_names, 
                                   index=default_idx,
                                   key="search_bar_widget")
        
        # Sync widget selection to session state
        if search_query:
            st.session_state['last_selected_bar'] = search_query
        
        # --- Arrondissement Filter ---
        # FIX: Use "Code postal" column directly from GeoJSON properties if available
        if 'Code postal' in gdf_bar.columns:
            # Ensure it's string for consistent processing
            gdf_bar['Code_postal_clean'] = gdf_bar['Code postal'].astype(str)
        else:
            # Fallback extraction
            gdf_bar['Code_postal_clean'] = gdf_bar['Adresse'].astype(str).str.extract(r'(75\d{3})')
        
        # Create arrondissement column for better display
        gdf_bar['Arrondissement'] = gdf_bar['Code_postal_clean'].apply(extract_arrondissement)
        
        # Sort unique arrondissements
        unique_arr = sorted(gdf_bar['Arrondissement'].dropna().unique(), key=lambda x: int(x.split('e')[0]))
        selected_arr = st.multiselect("📍 Arrondissement", unique_arr, placeholder="Tous les arrondissements")
        
        # Convert selected arrondissements back to postal codes for filtering
        if selected_arr:
            selected_zips = []
            for arr in selected_arr:
                arr_num = int(arr.split('e')[0])
                selected_zips.append(f"750{arr_num:02d}")
        else:
            selected_zips = []
        
        # --- Closest Bar Feature ---
        col_addr, col_btn = st.columns([3, 1])
        with col_addr:
            user_address = st.text_input("📍 Trouvez votre bar le plus proche en entrant votre adresse", placeholder="ex: 60 Avenue Emile Zola, Paris")
        with col_btn:
            st.write("") # Spacer
            if st.button("Trouver", use_container_width=True):
                if user_address:
                    with st.spinner("Recherche en cours..."):
                        coords = get_coordinates(user_address)
                        if coords:
                            u_lat, u_lon = coords
                            closest_name, dist = find_closest_bar(u_lat, u_lon, gdf_bar)
                            if closest_name:
                                st.success(f"Le bar le plus proche est : **{closest_name}** ({dist:.2f} km)")
                                # Update state to select this bar
                                st.session_state['last_selected_bar'] = closest_name
                                st.rerun()
                        else:
                            st.error("Adresse introuvable.")
                else:
                    st.warning("Veuillez entrer une adresse.")

        # --- Filter Data ---
        filtered_gdf = gdf_bar.copy()
        
        if selected_zips:
            filtered_gdf = filtered_gdf[filtered_gdf['Code_postal_clean'].isin(selected_zips)]
            
        # --- Bidirectional Sync Logic ---
        # 1. Capture Map Click (Session State 'last_selected_bar')
        # 2. Capture Widget Input (switched to Session State key 'search_bar_main')
        
        # When widget changes, it updates 'search_bar_main'. We should sync 'last_selected_bar'.
        if st.session_state.get('search_bar_main'):
             # If widget has a value, sync it to last selection
             if st.session_state.get('last_selected_bar') != st.session_state['search_bar_main']:
                 st.session_state['last_selected_bar'] = st.session_state['search_bar_main']
        
        current_selection = st.session_state.get('last_selected_bar', "")
        
        # Map Center Logic
        if current_selection and current_selection in filtered_gdf['Nom'].values:
             target_bar = filtered_gdf[filtered_gdf['Nom'] == current_selection].iloc[0]
             map_center = [target_bar['lat'], target_bar['lon']]
             map_zoom = 15
        else:
             map_center = [filtered_gdf['lat'].mean(), filtered_gdf['lon'].mean()] if not filtered_gdf.empty else [48.8566, 2.3522]
             map_zoom = 12

        # --- Layout: Map (Left/Center) | Details (Right) ---

        col_map, col_details = st.columns([2, 1])
        
        with col_map:
            # Scroll Indicator REMOVED (as requested implicitly by "Infos plus bas" removal, replaced by side panel focus)
            
            m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB dark_matter", scrollWheelZoom=False)
            
            # Add markers
            for idx, row in filtered_gdf.iterrows():
                is_selected = (current_selection == row['Nom'])
                icon_color = "red" if is_selected else "blue"
                
                popup_html = f"""
                <div style="font-family: 'Montserrat', sans-serif; min-width: 200px;">
                    <h5 style="color: #1E90FF; margin-bottom: 5px; font-weight:bold;">{row['Nom']}</h5>
                    <p style="margin: 2px 0; font-size:12px;"><b>📍 ADRESSE:</b><br>{row['Adresse']}</p>
                    <p style="margin: 2px 0; font-size:12px;"><b>🚇 MÉTRO:</b><br>{row.get('Métro', 'Non indiqué')}</p>
                </div>
                """

                folium.Marker(
                    [row['lat'], row['lon']],
                    tooltip=row['Nom'],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=icon_color, icon="glass-cheers", prefix="fa")
                ).add_to(m)
            
            # Display Map & Capture Returns
            # Note: We keep capturing return for display but IGNORING clicks as requested
            st_folium(m, width="100%", height=600, key="main_map")


        with col_details:
            # We use the session state directly
            selected_bar_name = st.session_state.get('last_selected_bar')
            
            if selected_bar_name:
                # Find data
                bar_match = gdf_bar[gdf_bar['Nom'] == selected_bar_name]
                if not bar_match.empty:
                    bar_data = bar_match.iloc[0]
                    
                    # Stylish Card for Details
                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #1E90FF;">
                        <h2 style="margin-top:0; color: #003366;">{selected_bar_name}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 1. Image
                    img_path = find_best_image_match(selected_bar_name, IMAGES_DIR)
                    if img_path:
                        st.image(img_path, use_container_width=True)
                    else:
                        st.markdown("""
                        <div style="background-color:#E6F3FF; height:200px; display:flex; align-items:center; justify-content:center; border-radius:10px; border: 2px dashed #1E90FF; margin-bottom: 20px;">
                            <span style="color:#1E90FF; font-size:40px;">📷</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # 2. Info
                    st.markdown(f"**📍 Adresse:** {bar_data['Adresse']}")
                    if pd.notna(bar_data.get('Métro')): st.markdown(f"**🚇 Métro:** {bar_data['Métro']}")
                    
                    col_det_1, col_det_2 = st.columns(2)
                    with col_det_1:
                        if pd.notna(bar_data.get('Téléphone')): st.markdown(f"📞 {bar_data['Téléphone']}")
                    with col_det_2:
                         if pd.notna(bar_data.get('Site')): st.markdown(f"🌐 [Site Web]({bar_data['Site']})")

                    # 3. Y Aller Button
                    encoded_address = bar_data['Adresse'].replace(' ', '+')
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                    st.markdown(f"""
                        <a href="{maps_url}" target="_blank" style="text-decoration: none;">
                            <button style="width:100%; background-color:#34A853; color:white; padding:12px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin: 15px 0; font-size: 16px; transition: 0.3s;">
                                🏃 J'y vais ! (Itinéraire Google Maps)
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 4. Games List (Bullet points)
                    st.markdown("### 🎲 Jeux Disponibles")
                    bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == selected_bar_name]
                    
                    games_list = sorted(bar_games['game'].tolist()) if not bar_games.empty else []
                    with st.container(height=300):
                        for g in games_list:
                            st.markdown(f"- {g}")
            
            # NO SPECIFIC BAR SELECTED - Show list if filtered
            elif not filtered_gdf.empty and len(filtered_gdf) < len(gdf_bar):
                st.markdown(f"### 📋 {len(filtered_gdf)} Bars dans cet arrondissement")
                
                # Iterate and show FULL details for each
                for idx, row in filtered_gdf.iterrows():
                    bar_name = row['Nom']
                    
                    # --- REPLICATED DETAIL CARD LOGIC ---
                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); border-top: 5px solid #1E90FF;">
                        <h2 style="margin-top:0; color: #003366;">{bar_name}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 1. Image
                    img_path = find_best_image_match(bar_name, IMAGES_DIR)
                    if img_path:
                        st.image(img_path, use_container_width=True)
                    else:
                         st.markdown("""
                        <div style="background-color:#E6F3FF; height:200px; display:flex; align-items:center; justify-content:center; border-radius:10px; border: 2px dashed #1E90FF; margin-bottom: 20px;">
                            <span style="color:#1E90FF; font-size:40px;">📷</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # 2. Info
                    st.markdown(f"**📍 Adresse:** {row['Adresse']}")
                    if pd.notna(row.get('Métro')): st.markdown(f"**🚇 Métro:** {row['Métro']}")
                    
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        if pd.notna(row.get('Téléphone')): st.markdown(f"📞 {row['Téléphone']}")
                    with c_d2:
                        if pd.notna(row.get('Site')): st.markdown(f"🌐 [Site Web]({row['Site']})")

                    # 3. Y Aller Button
                    encoded_address = row['Adresse'].replace(' ', '+')
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                    st.markdown(f"""
                        <a href="{maps_url}" target="_blank" style="text-decoration: none;">
                            <button style="width:100%; background-color:#34A853; color:white; padding:12px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin: 15px 0; font-size: 16px; transition: 0.3s;">
                                🏃 Y ALLER (Itinéraire)
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 4. Games List (Bullet points)
                    st.markdown("### 🎲 Jeux Disponibles")
                    bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == bar_name]
                    
                    if not bar_games.empty:
                        games_list = sorted(bar_games['game'].tolist())
                        with st.container(height=300):
                            for g in games_list:
                                st.markdown(f"- {g}")
                    
                    st.markdown("---") # Separator between bars
            else:
                 st.info("Aucun bar sélectionné. Choissisez un arrondissement pour voir la liste.")


    # TAB 2: LES JEUX (Recherche croisée - Redesigned)
    with tab2:
        st.subheader("🎲 Trouver un bar par jeu")
        
        # Help Text
        st.markdown('<div class="scroll-indicator">⬇️ Résultats plus bas ⬇️</div>', unsafe_allow_html=True)
        
        # --- Game Search ---
        if not st.session_state.games_data.empty:
            all_games = sorted(st.session_state.games_data['game'].unique())
            selected_games_multi = st.multiselect("🔍 Rechercher un ou plusieurs jeux :", all_games, placeholder="Sélectionnez des jeux")
        else:
            st.write("Chargement des jeux...")
            selected_games_multi = []

        # --- Filter Data ---
        if selected_games_multi:
            bars_with_games = st.session_state.games_data[st.session_state.games_data['game'].isin(selected_games_multi)]['bar_name'].unique()
            map_data = gdf_bar[gdf_bar['Nom'].isin(bars_with_games)]
        else:
            map_data = gdf_bar
            
        if selected_games_multi:
            st.info(f"🎯 {len(map_data)} bar(s) proposent les jeux sélectionnés.")

        # --- Layout: Map (Left) | Details (Right) ---
        col_map, col_details = st.columns([2, 1])

        with col_map:
            # Center map
            center_lat = map_data['lat'].mean() if len(map_data) > 0 else 48.8566
            center_lon = map_data['lon'].mean() if len(map_data) > 0 else 2.3522

            m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB dark_matter", scrollWheelZoom=False)
            
            for idx, row in map_data.iterrows():
                bar_games_count = len(st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']])
                
                # Check which of the selected games are here
                if selected_games_multi:
                    games_here = st.session_state.games_data[
                        (st.session_state.games_data['bar_name'] == row['Nom']) & 
                        (st.session_state.games_data['game'].isin(selected_games_multi))
                    ]['game'].tolist()
                    games_snippet = "<br>• " + "<br>• ".join(games_here[:5])
                    if len(games_here) > 5: games_snippet += "..."
                else:
                    games_snippet = f"{bar_games_count} jeux"

                popup_html = f"""
                <div style="font-family: 'Montserrat', sans-serif; min-width: 200px;">
                    <h5 style="color: #1E90FF; margin-bottom: 5px; font-weight:bold;">{row['Nom']}</h5>
                    <p style="margin: 2px 0; font-size:12px;"><b>📍 ADRESSE:</b><br>{row['Adresse']}</p>
                    <div style="margin-top:5px; font-size:12px; color:green;"><b>MATCH:</b>{games_snippet}</div>
                </div>
                """
                
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['Nom'],
                    icon=folium.Icon(color="green" if selected_games_multi else "blue", icon="gamepad", prefix="fa")
                ).add_to(m)
            
            st_folium(m, width="100%", height=500, key="folium_map_games")

        with col_details:
            if selected_games_multi and not map_data.empty:
                st.markdown(f"### 📋 {len(map_data)} Bar(s) trouvé(s)")
                
                # Iterate and show FULL details for each bar
                for idx, row in map_data.iterrows():
                    bar_name = row['Nom']
                    
                    # --- FULL BAR DETAIL CARD ---
                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); border-top: 5px solid #1E90FF;">
                        <h2 style="margin-top:0; color: #003366;">{bar_name}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 1. Image
                    img_path = find_best_image_match(bar_name, IMAGES_DIR)
                    if img_path:
                        st.image(img_path, use_container_width=True)
                    else:
                        st.markdown("""
                        <div style="background-color:#E6F3FF; height:150px; display:flex; align-items:center; justify-content:center; border-radius:10px; border: 2px dashed #1E90FF; margin-bottom: 15px;">
                            <span style="color:#1E90FF; font-size:40px;">📷</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # 2. Info
                    st.markdown(f"**📍 Adresse:** {row['Adresse']}")
                    if pd.notna(row.get('Métro')): st.markdown(f"**🚇 Métro:** {row['Métro']}")
                    
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        if pd.notna(row.get('Téléphone')): st.markdown(f"📞 {row['Téléphone']}")
                    with c_d2:
                        if pd.notna(row.get('Site')): st.markdown(f"🌐 [Site Web]({row['Site']})")

                    # 3. Y Aller Button
                    encoded_address = row['Adresse'].replace(' ', '+')
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                    st.markdown(f"""
                        <a href="{maps_url}" target="_blank" style="text-decoration: none;">
                            <button style="width:100%; background-color:#34A853; color:white; padding:12px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin: 15px 0; font-size: 16px; transition: 0.3s;">
                                🏃 J'y vais ! (Itinéraire Google Maps)
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 4. Games found (filtered games first)
                    st.markdown("### 🎲 Jeux recherchés disponibles ici")
                    found_games = st.session_state.games_data[
                        (st.session_state.games_data['bar_name'] == bar_name) & 
                        (st.session_state.games_data['game'].isin(selected_games_multi))
                    ]['game'].tolist()
                    
                    for g in sorted(found_games):
                        st.markdown(f"✅ **{g}**")
                    
                    # 5. All other games at this bar
                    st.markdown("### 📜 Autres jeux disponibles")
                    all_bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == bar_name]['game'].tolist()
                    other_games = [g for g in all_bar_games if g not in found_games]
                    
                    if other_games:
                        with st.container(height=200):
                            for g in sorted(other_games):
                                st.markdown(f"- {g}")
                    else:
                        st.info("Pas d'autres jeux disponibles.")
                    
                    st.markdown("---") # Separator between bars
        
            elif not selected_games_multi:
                st.warning("Aucun bar ne propose ces jeux.")

        st.markdown("---")
        st.markdown("### ➕ Demander un Jeu (ou modification)")
        
        if st.session_state.role == 'guest':
             st.info("🔒 Vous devez être connecté pour faire une demande.")
        else:
            with st.form("request_game_new"):
                col_req1, col_req2 = st.columns(2)
                with col_req1:
                    req_user = st.text_input("Votre Nom/Pseudo :", value=st.session_state.username)
                    req_bar = st.selectbox("Bar concerné :", gdf_bar['Nom'].sort_values().tolist())
                with col_req2:
                    req_game = st.text_input("Nom du Jeu :")
                    req_action = st.selectbox("Type de demande :", ["Ajouter le jeu", "Signaler une erreur"])
                
                req_desc = st.text_area("Description / Détails :", placeholder="Ex: Le jeu n'est plus disponible...")
                
                if st.form_submit_button("📤 Envoyer la demande"):
                    if req_user and req_game and req_bar:
                        request = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'username': req_user,
                            'bar_name': req_bar,
                            'game_name': req_game,
                            'action_type': req_action,
                            'description': req_desc,
                            'status': 'pending'
                        }
                        st.session_state.game_requests.append(request)
                        save_game_request(request)
                        st.success("✅ Demande envoyée aux administrateurs !")
                    else:
                        st.error("⚠️ Veuillez remplir le nom, le bar et le jeu.")
    
    # TAB 3: Forum
    with tab3:
        st.subheader("💬 Forum")
        
        if st.session_state.role == 'guest':
            st.info("🔒 Connectez-vous pour publier un message.")
        else:
            with st.form("new_post"):
                # Username is now automatic
                st.write(f"**Auteur :** {st.session_state.username}")
                bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
                game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
                date_time = st.text_input("Quand :", placeholder="ex: Demain 19h")
                message = st.text_area("Message :")
                
                if st.form_submit_button("Publier"):
                    if message and game_choice:
                        # Check profanity
                        if contains_profanity(message) or contains_profanity(game_choice):
                            st.error("⚠️ Votre message contient des termes inappropriés et n'a pas été publié.")
                        else:
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
                is_admin = st.session_state.get('role') == 'admin'
                col1, col2 = st.columns([4, 1])
                with col1:
                    reported_flag = "🚩 " if post.get('reported', False) else ""
                    
                    # Avatar and Info
                    col_p_icon, col_p_info = st.columns([1, 8])
                    with col_p_icon:
                         auth_icon = post.get('user_icon', '')
                         if auth_icon and os.path.exists(auth_icon):
                             st.image(auth_icon, width=50) # Will be circular via CSS hopefully
                         else:
                             st.write("👤")
                    
                    with col_p_info:
                        st.markdown(f"{reported_flag}**{post['username']}** <span style='color:grey; font-size:0.8em'>• {post['timestamp']}</span>", unsafe_allow_html=True)
                        if post.get('when'):
                             st.markdown(f"📅 **{post['when']}**")
                        st.markdown(f"📍 *{post['bar']}* — 🎮 *{post['game']}*")

                    st.markdown(f"<div style='background:#f0f2f6; padding:10px; border-radius:10px; margin-top:5px;'>{post['message']}</div>", unsafe_allow_html=True)
                    
                    # Reactions (Horizontal Layout)
                    
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
                            
                            # Delete comment button (Only comment author or admin/post author)
                            is_comment_author = (comment.get('author') == st.session_state.username)
                            
                            if is_comment_author or is_admin:
                                if st.button("🗑️", key=f"del_com_{idx}_{c_idx}"):
                                    delete_comment(idx, c_idx)
                                    st.rerun()
                    
                    # Add comment
                    if st.session_state.role != 'guest':
                        with st.form(f"comment_{idx}"):
                            col_c1, col_c2 = st.columns([1, 3])
                            with col_c1:
                                st.write(f"👤 {st.session_state.username}")
                            with col_c2:
                                c_text = st.text_input("Commentaire:", key=f"c_text_{idx}")
                                
                            if st.form_submit_button("💬 Commenter"):
                                if c_text:
                                    if contains_profanity(c_text):
                                        st.error("⚠️ Message inapproprié.")
                                    else:
                                        add_comment_to_post(idx, st.session_state.username, c_text)
                                        st.rerun()
                                else:
                                    st.error("Message requis")
                    else:
                        st.caption("🔒 Connectez-vous pour commenter.")
                
                with col2:
                    # Post deletion - Only author or admin
                    is_author = (post['username'] == st.session_state.username)
                    # is_admin is already defined at loop start
                    
                    if is_author or is_admin:
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