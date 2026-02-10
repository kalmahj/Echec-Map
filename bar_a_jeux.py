# -*- coding: utf-8 -*-
"""
Echec et Map — Recherche de Bars à Jeux à Paris
Main application entry point.
"""
import streamlit as st
import pandas as pd
import json
import os
import base64
import random
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- Module imports ---
from modules.config import (
    LOGO_PATH, IMAGES_DIR, USERS_JSON_PATH, ICONS_DIR, BASE_DIR
)
from modules.utils import (
    find_closest_bar, get_coordinates, extract_arrondissement, find_best_image_match
)
from modules.auth import (
    load_users, verify_user, contains_profanity
)
from modules.data import (
    load_data, load_games_from_csv, load_forum_comments, load_game_requests
)
from modules.forum import (
    save_forum_comment, save_game_request,
    add_reaction, add_comment_to_post, delete_comment,
    delete_forum_post, report_forum_post,
    approve_game_request, reject_game_request
)
from modules.components import render_bar_detail_card, render_login_page

# ============================================================
# PAGE CONFIG
# ============================================================
page_icon = "🎮"
if os.path.exists(LOGO_PATH):
    page_icon = LOGO_PATH

st.set_page_config(
    page_title="Echec et Map",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# LOAD THEME CSS
# ============================================================
from modules.config import THEME_CSS_PATH
if os.path.exists(THEME_CSS_PATH):
    with open(THEME_CSS_PATH, 'r', encoding='utf-8') as css_file:
        theme_css = css_file.read()
    st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION — Default to guest (no login wall)
# ============================================================
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
    st.session_state.logged_in = True      # Auto-login as guest
if 'username' not in st.session_state:
    st.session_state.username = "Invité"   # Default guest name
if 'user_icon' not in st.session_state:
    st.session_state.user_icon = ""
if 'role' not in st.session_state:
    st.session_state.role = "guest"        # Default guest role
if 'show_login_form' not in st.session_state:
    st.session_state.show_login_form = False

# ============================================================
# SESSION PERSISTENCE (restore login from query params)
# ============================================================
if st.session_state.role == 'guest':
    qp = st.query_params
    if "session_user" in qp:
        saved_user = qp["session_user"]
        try:
            if os.path.exists(USERS_JSON_PATH):
                with open(USERS_JSON_PATH, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    user = next((u for u in users if u['username'] == saved_user), None)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = saved_user
                        st.session_state.role = user.get('role', 'user')
                        st.session_state.user_icon = user.get('icon', '')
                        if st.session_state.role == 'admin':
                            st.session_state.admin_logged_in = True
                            st.session_state.show_admin_panel = True
                        st.toast(f"Session restaurée : Bon retour {saved_user} !", icon="🔄")
        except:
            pass

# ============================================================
# LOAD DATA
# ============================================================
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()
    # Parse JSON comments on load
    for post in st.session_state.forum_posts:
        if 'comments' in post and isinstance(post['comments'], str):
            try:
                post['comments'] = json.loads(post['comments'])
            except:
                if '|||' in post['comments']:
                    legacy = post['comments'].split('|||')
                    post['comments'] = [{'author': 'Anonyme', 'text': c, 'timestamp': ''} for c in legacy if c]
                else:
                    post['comments'] = []

if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()
if len(st.session_state.game_requests) == 0:
    st.session_state.game_requests = load_game_requests()

# ============================================================
# HEADER WITH PROFILE / LOGIN BUTTON (top-right)
# ============================================================
col_header, col_user = st.columns([2, 1])

with col_header:
    if os.path.exists(LOGO_PATH):
        # Read and encode the local image to base64
        with open(LOGO_PATH, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        
        # Create an HTML anchor tag with the image inside
        # Replace the href URL with your actual landing page URL
        logo_html = f"""
            <a href="https://echec-map.streamlit.app/" target="_self">
                <img src="data:image/png;base64,{data}" width="200" style="cursor: pointer;">
            </a>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
    else:
        st.markdown("<h1>🎮 Echec et Map</h1>", unsafe_allow_html=True)

with col_user:
    if st.session_state.role != 'guest':
        # --- Logged-in user: show avatar + name + logout ---
        col_avatar, col_name = st.columns([1, 2])

        with col_avatar:
            user_icon_path = st.session_state.user_icon
            if user_icon_path and os.path.exists(user_icon_path):
                st.image(user_icon_path, width=50)
            else:
                st.markdown("👤", unsafe_allow_html=True)

        with col_name:
            st.markdown(f"<div style='padding-top: 0.5rem;'><b>{st.session_state.username}</b></div>", unsafe_allow_html=True)
            if st.button("Se déconnecter", key="logout_btn", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "Invité"
                st.session_state.role = "guest"
                st.session_state.user_icon = ""
                st.session_state.admin_logged_in = False
                st.session_state.show_admin_panel = False
                if "session_user" in st.query_params:
                    del st.query_params["session_user"]
                st.rerun()
    else:
        # --- Guest: show login/register button ---
        if st.button("🔑 Connexion / Inscription", key="top_login_btn", use_container_width=True):
            st.session_state.show_login_form = not st.session_state.show_login_form

# --- Expandable Login/Register Form (slides down below header) ---
if st.session_state.get('show_login_form', False) and st.session_state.role == 'guest':
    with st.container():
        render_login_page()
    st.stop()
else:
    st.markdown("---")

# ============================================================
# MAIN APP
# ============================================================
try:
    gdf_bar = load_data()

    # --- Assign random games to bars without games ---
    all_bar_names = gdf_bar['Nom'].tolist()
    bars_with_games = st.session_state.games_data['bar_name'].unique().tolist() if not st.session_state.games_data.empty else []
    bars_without_games = [b for b in all_bar_names if b not in bars_with_games]

    if bars_without_games and not st.session_state.games_data.empty:
        all_available_games = st.session_state.games_data['game'].unique().tolist()
        new_entries = []
        for bar_name in bars_without_games:
            if len(all_available_games) > 100:
                random_games = random.sample(all_available_games, 100)
            else:
                random_games = all_available_games
            for game in random_games:
                new_entries.append({'bar_name': bar_name, 'game': game})

        if new_entries:
            new_df = pd.DataFrame(new_entries)
            st.session_state.games_data = pd.concat([st.session_state.games_data, new_df], ignore_index=True)

    # ============================================================
    # TABS
    # ============================================================
    if st.session_state.admin_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🍷 Les Bars", "🎲 Les Jeux", "💬 Forum", "🔧 Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["🍷 Les Bars", "🎲 Les Jeux", "💬 Forum"])

    # ============================================================
    # TAB 1: LES BARS
    # ============================================================
    with tab1:
        st.subheader("🍷 Carte des Bars")

        col_help, col_reset = st.columns([3, 1])
        with col_help:
            st.markdown('<div class="scroll-indicator">⬇️ Résultats plus bas ⬇️</div>', unsafe_allow_html=True)
        with col_reset:
            if st.button("🔄 Réinitialiser la carte", use_container_width=True):
                st.session_state['last_selected_bar'] = ""
                st.session_state['search_bar_main'] = ""
                st.rerun()

        # --- Callbacks for State Management ---
        def on_arr_change():
            # If arrondissement filter changes, clear specific bar selection
            st.session_state['last_selected_bar'] = ""
            st.session_state['search_bar_main'] = ""

        def on_search_change():
            # If specific bar searched, clear arrondissement filter to ensure visibility
            if st.session_state.get('search_bar_main'):
                st.session_state['last_selected_bar'] = st.session_state['search_bar_main']
                st.session_state['arr_filter'] = []

        # --- Search Bar ---
        all_bar_names_sorted = sorted(gdf_bar['Nom'].tolist())
        default_idx = 0
        
        
        # Sync from Map Click (update widget state before instantiation)
        if st.session_state.get("update_search_bar", False):
            st.session_state["search_bar_main"] = st.session_state.get("last_selected_bar", "")
            st.session_state["update_search_bar"] = False
            
        # Check for filter reset flag
        if st.session_state.get("reset_arr_filter", False):
            st.session_state["arr_filter"] = []
            st.session_state["reset_arr_filter"] = False
            
        if st.session_state.get('last_selected_bar') in all_bar_names_sorted:
            default_idx = all_bar_names_sorted.index(st.session_state['last_selected_bar']) + 1

        # search_query = st.selectbox(
        #     "🔍 Rechercher un bar spécifique :",
        #     options=[""] + all_bar_names_sorted,
        #     index=default_idx,
        #     key="search_bar_main",
        #     on_change=on_search_change
        # )

        search_query = []

        if search_query:
            st.session_state['last_selected_bar'] = search_query

        # --- Arrondissement Filter ---
        if 'Code postal' in gdf_bar.columns:
            gdf_bar['Code_postal_clean'] = gdf_bar['Code postal'].astype(str)
        else:
            gdf_bar['Code_postal_clean'] = gdf_bar['Adresse'].astype(str).str.extract(r'(75\d{3})')

        gdf_bar['Arrondissement'] = gdf_bar['Code_postal_clean'].apply(extract_arrondissement)

        unique_arr = sorted(gdf_bar['Arrondissement'].dropna().unique(), key=lambda x: int(x.split('e')[0]))
        
        # Ensure 'arr_filter' key is used and synced
        selected_arr = st.multiselect(
            "📍 Arrondissement", 
            unique_arr, 
            placeholder="Tous les arrondissements",
            key="arr_filter",
            on_change=on_arr_change
        )

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
            st.write("")
            if st.button("Trouver", use_container_width=True):
                if user_address:
                    with st.spinner("Recherche en cours..."):
                        coords = get_coordinates(user_address)
                        if coords:
                            u_lat, u_lon = coords
                            closest_name, dist = find_closest_bar(u_lat, u_lon, gdf_bar)
                            if closest_name:
                                st.success(f"Le bar le plus proche est : **{closest_name}** ({dist:.2f} km)")
                                st.session_state['last_selected_bar'] = closest_name
                                st.session_state['search_bar_main'] = closest_name
                                st.session_state['reset_arr_filter'] = True # Set flag to clear filter on next run
                                st.rerun()
                        else:
                            st.error("Adresse introuvable.")
                else:
                    st.warning("Veuillez entrer une adresse.")

        # --- Filter Data ---
        filtered_gdf = gdf_bar.copy()
        if selected_zips:
            filtered_gdf = filtered_gdf[filtered_gdf['Code_postal_clean'].isin(selected_zips)]

        # --- Bidirectional Sync ---
        if 'search_bar_main' in st.session_state:
            if st.session_state['search_bar_main']:
                if st.session_state.get('last_selected_bar') != st.session_state['search_bar_main']:
                    st.session_state['last_selected_bar'] = st.session_state['search_bar_main']
                    st.session_state['just_found_closest'] = False
            elif st.session_state['search_bar_main'] == "" and not st.session_state.get('just_found_closest', False):
                st.session_state['last_selected_bar'] = ""

        current_selection = st.session_state.get('last_selected_bar', "")

        # Map Center
        if current_selection and current_selection in filtered_gdf['Nom'].values:
            target_bar = filtered_gdf[filtered_gdf['Nom'] == current_selection].iloc[0]
            map_center = [target_bar['lat'], target_bar['lon']]
            map_zoom = 15
        else:
            map_center = [filtered_gdf['lat'].mean(), filtered_gdf['lon'].mean()] if not filtered_gdf.empty else [48.8566, 2.3522]
            map_zoom = 12

        # --- Map + Details Layout ---
        col_map, col_details = st.columns([2, 1])

        with col_map:
            m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB dark_matter", scrollWheelZoom=False)
            for idx, row in filtered_gdf.iterrows():
                is_selected = (current_selection == row['Nom'])
                icon_color = "red" if is_selected else "blue"

                popup_html = f"""
                <div style="font-family: 'Inter', sans-serif; min-width: 200px; background:#1C1C1E; color:#fff; padding:10px; border-radius:10px;">
                    <h5 style="color: #007AFF; margin-bottom: 5px; font-weight:bold;">{row['Nom']}</h5>
                    <p style="margin: 2px 0; font-size:12px; color:#ccc;"><b>📍 ADRESSE:</b><br>{row['Adresse']}</p>
                    <p style="margin: 2px 0; font-size:12px; color:#ccc;"><b>🚇 MÉTRO:</b><br>{row.get('Métro', 'Non indiqué')}</p>
                </div>
                """

                folium.Marker(
                    [row['lat'], row['lon']],
                    tooltip=row['Nom'],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=icon_color, icon="glass-cheers", prefix="fa")
                ).add_to(m)

            map_data = st_folium(m, width="100%", height=600, key="main_map")

            # --- Detect Map Click ---
            if map_data and map_data.get("last_object_clicked_tooltip"):
                clicked_name = map_data["last_object_clicked_tooltip"]
                # Check if it's a valid bar and different from current selection
                if clicked_name in all_bar_names_sorted:
                    if clicked_name != st.session_state.get("last_selected_bar"):
                        st.session_state["last_selected_bar"] = clicked_name
                        st.session_state["update_search_bar"] = True  # Sync dropdown on next run
                        st.session_state["reset_arr_filter"] = True # Set flag to clear filter on next run
                        st.rerun()

        with col_details:
            selected_bar_name = st.session_state.get('last_selected_bar')

            if selected_bar_name:
                bar_match = gdf_bar[gdf_bar['Nom'] == selected_bar_name]
                if not bar_match.empty:
                    bar_data = bar_match.iloc[0]
                    render_bar_detail_card(bar_data, selected_bar_name, st.session_state.games_data, 0, "sel")

            elif not filtered_gdf.empty and len(filtered_gdf) < len(gdf_bar):
                st.markdown(f"### 📋 {len(filtered_gdf)} Bars dans cet arrondissement")
                for idx, row in filtered_gdf.iterrows():
                    render_bar_detail_card(row, row['Nom'], st.session_state.games_data, idx, "list")
                    st.markdown("---")
            else:
                st.info("Aucun bar sélectionné. Choissisez un arrondissement pour voir la liste.")

    # ============================================================
    # TAB 2: LES JEUX
    # ============================================================
    with tab2:
        st.subheader("🎲 Trouver un bar par jeu")

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
            bars_with_sel_games = st.session_state.games_data[st.session_state.games_data['game'].isin(selected_games_multi)]['bar_name'].unique()
            map_data = gdf_bar[gdf_bar['Nom'].isin(bars_with_sel_games)]
        else:
            map_data = gdf_bar

        if selected_games_multi:
            st.info(f"🎯 {len(map_data)} bar(s) proposent les jeux sélectionnés.")

        # --- Map + Details Layout ---
        col_map2, col_details2 = st.columns([2, 1])

        with col_map2:
            center_lat = map_data['lat'].mean() if len(map_data) > 0 else 48.8566
            center_lon = map_data['lon'].mean() if len(map_data) > 0 else 2.3522

            m2 = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB dark_matter", scrollWheelZoom=False)

            for idx, row in map_data.iterrows():
                bar_games_count = len(st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']])

                if selected_games_multi:
                    games_here = st.session_state.games_data[
                        (st.session_state.games_data['bar_name'] == row['Nom']) &
                        (st.session_state.games_data['game'].isin(selected_games_multi))
                    ]['game'].tolist()
                    games_snippet = "<br>• " + "<br>• ".join(games_here[:5])
                    if len(games_here) > 5:
                        games_snippet += "..."
                else:
                    games_snippet = f"{bar_games_count} jeux"

                popup_html = f"""
                <div style="font-family: 'Inter', sans-serif; min-width: 200px; background:#1C1C1E; color:#fff; padding:10px; border-radius:10px;">
                    <h5 style="color: #007AFF; margin-bottom: 5px; font-weight:bold;">{row['Nom']}</h5>
                    <p style="margin: 2px 0; font-size:12px; color:#ccc;"><b>📍 ADRESSE:</b><br>{row['Adresse']}</p>
                    <div style="margin-top:5px; font-size:12px; color:#34C759;"><b>MATCH:</b>{games_snippet}</div>
                </div>
                """

                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['Nom'],
                    icon=folium.Icon(color="green" if selected_games_multi else "blue", icon="gamepad", prefix="fa")
                ).add_to(m2)

            st_folium(m2, width="100%", height=500, key="folium_map_games")

        with col_details2:
            if selected_games_multi and not map_data.empty:
                st.markdown(f"### 📋 {len(map_data)} Bar(s) trouvé(s)")

                for idx, row in map_data.iterrows():
                    bar_name = row['Nom']

                    render_bar_detail_card(row, bar_name, st.session_state.games_data, idx, "games")

                    # Show matched games specifically
                    st.markdown("### 🎲 Jeux recherchés disponibles ici")
                    found_games = st.session_state.games_data[
                        (st.session_state.games_data['bar_name'] == bar_name) &
                        (st.session_state.games_data['game'].isin(selected_games_multi))
                    ]['game'].tolist()

                    for g in sorted(found_games):
                        st.markdown(f"✅ **{g}**")

                    # Other games
                    st.markdown("### 📜 Autres jeux disponibles")
                    all_bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == bar_name]['game'].tolist()
                    other_games = [g for g in all_bar_games if g not in found_games]

                    if other_games:
                        with st.container(height=200):
                            for g in sorted(other_games):
                                st.markdown(f"- {g}")
                    else:
                        st.info("Pas d'autres jeux disponibles.")

                    st.markdown("---")

            elif selected_games_multi and map_data.empty:
                st.warning("🔍 Aucun bar ne propose ces jeux. Essayez avec d'autres jeux ou faites une demande ci-dessous !")
            else:
                st.info("Sélectionnez un ou plusieurs jeux à gauche pour afficher les bars qui les proposent.")

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

    # ============================================================
    # TAB 3: FORUM
    # ============================================================
    with tab3:
        st.subheader("💬 Forum")

        if st.session_state.role == 'guest':
            st.info("🔒 Connectez-vous pour publier un message.")
        else:
            with st.form("new_post"):
                st.write(f"**Auteur :** {st.session_state.username}")
                bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
                game_choice = st.text_input("Jeu :", placeholder="Tapez le nom du jeu")
                date_time = st.text_input("Quand :", placeholder="ex: Demain 19h")
                message = st.text_area("Message :")

                if st.form_submit_button("Publier"):
                    if message and game_choice:
                        if contains_profanity(message) or contains_profanity(game_choice):
                            st.error("⚠️ Votre message contient des termes inappropriés et n'a pas été publié.")
                        else:
                            post = {
                                'username': st.session_state.username,
                                'user_icon': st.session_state.user_icon,
                                'bar': bar_choice,
                                'game': game_choice,
                                'when': date_time,
                                'message': message,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'reported': False,
                                'report_reason': '',
                                'reactions': '',
                                'comments': []
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

                    col_p_icon, col_p_info = st.columns([1, 8])
                    with col_p_icon:
                        auth_icon = post.get('user_icon', '')
                        if auth_icon and os.path.exists(auth_icon):
                            st.image(auth_icon, width=50)
                        else:
                            st.write("👤")

                    with col_p_info:
                        st.markdown(f"{reported_flag}**{post['username']}** <span style='color:#8E8E93; font-size:0.8em'>• {post['timestamp']}</span>", unsafe_allow_html=True)
                        if post.get('when'):
                            st.markdown(f"📅 **{post['when']}**")
                        st.markdown(f"📍 *{post['bar']}* — 🎮 *{post['game']}*")

                    st.markdown(f"<div style='background:#2C2C2E; color:#fff; padding:0.75rem; border-radius:0.625rem; margin-top:0.3rem;'>{post['message']}</div>", unsafe_allow_html=True)

                    # Reactions
                    reactions = post.get('reactions', '')
                    if reactions:
                        if isinstance(reactions, str):
                            try:
                                reactions_dict = json.loads(reactions)
                                reaction_display = ' '.join([f"{emoji} {count}" for emoji, count in reactions_dict.items()])
                                st.markdown(f"**Réactions:** {reaction_display}")
                            except:
                                st.markdown(f"**Réactions:** {reactions}")
                        else:
                            st.markdown(f"**Réactions:** {reactions}")

                    st.markdown('<div class="reaction-container">', unsafe_allow_html=True)
                    cols = st.columns([1, 1, 1, 1, 6])
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
                    if isinstance(comments, str):
                        try:
                            comments = json.loads(comments)
                        except:
                            comments = []

                    if comments:
                        st.markdown("**Commentaires:**")
                        for c_idx, comment in enumerate(comments):
                            st.markdown(f"""
                            <div class="comment-box">
                                <div class="comment-header">
                                    <span class="comment-author">{comment.get('author', 'Anonyme')}</span>
                                    <span>{comment.get('timestamp', '')}</span>
                                </div>
                                <div class="comment-text">{comment.get('text', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)

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
                    is_author = (post['username'] == st.session_state.username)
                    if is_author or is_admin:
                        if st.button("🗑️", key=f"del_post_{idx}", help="Supprimer mon post"):
                            delete_forum_post(idx)
                            st.success("Supprimé")
                            st.rerun()

                    if not post.get('reported', False):
                        if f"show_report_{idx}" not in st.session_state:
                            st.session_state[f"show_report_{idx}"] = False

                        if st.button("🚩 Signaler", key=f"toggle_report_{idx}"):
                            st.session_state[f"show_report_{idx}"] = not st.session_state[f"show_report_{idx}"]

                        if st.session_state[f"show_report_{idx}"]:
                            with st.form(f"report_form_{idx}"):
                                reason = st.text_input("Raison :")
                                if st.form_submit_button("Envoyer"):
                                    report_forum_post(idx, reason)
                                    st.session_state[f"show_report_{idx}"] = False
                                    st.success("Signalé à l'admin")
                                    st.rerun()

                st.markdown("---")

    # ============================================================
    # TAB 4: ADMIN
    # ============================================================
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
                    st.markdown(f"""<div style='border: 1px solid #FF3B30; padding: 0.75rem; border-radius: 0.625rem; background:#2C2C2E;'>
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
                            st.session_state.forum_posts[idx]['reported'] = False
                            save_forum_comment(st.session_state.forum_posts[idx])
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