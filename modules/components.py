# -*- coding: utf-8 -*-
"""
Reusable UI components: bar detail card, login page.
"""
import os
import time
import streamlit as st
import pandas as pd

from modules.config import IMAGES_DIR
from modules.utils import find_best_image_match, get_menu_pdf_path
from modules.auth import verify_user, create_user, get_available_icons


def render_bar_detail_card(bar_data, bar_name, games_data, idx, key_prefix="detail", show_games=True):
    """
    Render a full bar detail card with image, info, directions, menu, and games.
    
    Args:
        bar_data: Series/row with bar information
        bar_name: Name of the bar
        games_data: DataFrame with games data
        idx: Index for unique keys
        key_prefix: Prefix for Streamlit widget keys
        show_games: Whether to show the default games list section
    """
    # Header card
    st.markdown(f"""
    <div style="background-color: var(--color-surface, white); padding: 1.25rem; border-radius: var(--radius-lg, 10px); 
         box-shadow: 0 4px 8px rgba(0,0,0,0.15); border-top: 5px solid var(--color-accent, #007AFF); margin-bottom: 1rem;">
        <h2 style="margin-top:0; color: var(--color-text, #003366);">{bar_name}</h2>
    </div>
    """, unsafe_allow_html=True)

    # 1. Image
    img_path = find_best_image_match(bar_name, IMAGES_DIR)
    if img_path:
        st.image(img_path, use_container_width=True)
    else:
        st.markdown("""
        <div style="background-color: var(--color-surface-alt, #E6F3FF); height:200px; display:flex; 
             align-items:center; justify-content:center; border-radius: var(--radius-lg, 10px); 
             border: 2px dashed var(--color-accent, #007AFF); margin-bottom: 1.25rem;">
            <span style="font-size:2.5rem;">📷</span>
        </div>
        """, unsafe_allow_html=True)

    # 2. Info
    st.markdown(f"**📍 Adresse:** {bar_data['Adresse']}")
    if pd.notna(bar_data.get('Métro')):
        st.markdown(f"**🚇 Métro:** {bar_data['Métro']}")

    col_det_1, col_det_2 = st.columns(2)
    with col_det_1:
        if pd.notna(bar_data.get('Téléphone')):
            st.markdown(f"📞 {bar_data['Téléphone']}")
    with col_det_2:
        if pd.notna(bar_data.get('Site')):
            st.markdown(f"🌐 [Site Web]({bar_data['Site']})")

    # 3. Y Aller Button
    encoded_address = bar_data['Adresse'].replace(' ', '+')
    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
    st.markdown(f"""
        <a href="{maps_url}" target="_blank" style="text-decoration: none;">
            <button style="width:100%; background-color: var(--color-success, #34C759); color:white; 
                 padding: 0.75rem; border:none; border-radius: var(--radius-md, 8px); font-weight:bold; 
                 cursor:pointer; margin: 1rem 0; font-size: 1rem; transition: 0.3s;">
                🏃 J'y vais ! (Itinéraire Google Maps)
            </button>
        </a>
    """, unsafe_allow_html=True)

    # 4. Menu Button
    menu_path = get_menu_pdf_path(bar_name)
    if menu_path:
        with open(menu_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            st.download_button(
                label="📜 DÉCOUVRIR LE MENU",
                data=pdf_bytes,
                file_name=f"Menu_{bar_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"btn_menu_{idx}_{key_prefix}"
            )

    # 5. Games List (can be skipped when caller handles games separately)
    if show_games:
        st.markdown("### 🎲 Jeux Disponibles")
        bar_games = games_data[games_data['bar_name'] == bar_name]
        games_list = sorted(bar_games['game'].tolist()) if not bar_games.empty else []
        with st.container(height=300):
            for g in games_list:
                st.markdown(f"- {g}")


def render_login_page():
    """Render the login/register form (embedded in top-right expandable section)."""
    st.markdown("<h3 style='text-align: center;'>🔑 Connexion / Inscription</h3>", unsafe_allow_html=True)

    # Query Param Handling for Avatar Selection
    if "avatar_select" in st.query_params:
        selected_file = st.query_params["avatar_select"]
        # Find the full path from the filename
        icons = get_available_icons()
        match = next((i for i in icons if os.path.basename(i) == selected_file), None)
        if match:
            st.session_state.temp_selected_icon = match
            # Clear param and rerun to clean URL
            if "avatar_select" in st.query_params:
                del st.query_params["avatar_select"]
            st.rerun()

    # Determine Active Tab based on state
    # If we have a selected icon, default to Register tab being first/active to prevent switching back
    if st.session_state.get('temp_selected_icon'):
        tab2, tab1 = st.tabs(["Créer un compte", "Se connecter"])
    else:
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
                    st.session_state.show_login_form = False
                    if st.session_state.role == 'admin':
                        st.session_state.admin_logged_in = True
                        st.session_state.show_admin_panel = True
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

        # Display Avatars in a Grid (Clickable Images via HTML)
        # Display Avatars in a Responsive Grid (Matrix)
        # (re-import base64 just in case, though usually top-level is better, but local scope is fine)
        import base64
        
        # Helper function
        def get_img_as_base64_local(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()

        html_images = []
        for icon_p in icons:
            file_name = os.path.basename(icon_p)
            
            # Styles
            is_selected = (st.session_state.temp_selected_icon == icon_p)
            border_style = "3px solid var(--color-success, #34C759)" if is_selected else "3px solid transparent"
            opacity = "1.0" if is_selected else "0.8"
            scale = "1.1" if is_selected else "1.0"
            
            try:
                b64_str = get_img_as_base64_local(icon_p)
                # Note: No indentation for HTML strings to avoid code-block formatting in st.markdown
                img_block = f"""<div style="margin: 10px; text-align: center; transition: transform 0.2s;">
<a href="?avatar_select={file_name}" target="_self" style="text-decoration: none;">
<img src="data:image/png;base64,{b64_str}" 
style="width: 80px; height: 80px; object-fit: cover; border-radius: 50%; 
border: {border_style}; opacity: {opacity}; transform: scale({scale});
box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
onmouseover="this.style.opacity='1.0'; this.style.transform='scale(1.1)';" 
onmouseout="this.style.opacity='{opacity}'; this.style.transform='scale({scale})';"
/>
</a>
{f"<div style='color: var(--color-success, green); font-weight:bold; font-size:1.2rem; margin-top:-10px;'>✅</div>" if is_selected else ""}
</div>"""
                html_images.append(img_block)
            except:
                pass

        # Container with Flex/Grid behavior
        grid_html = f"""<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; padding: 10px;">
{''.join(html_images)}
</div>"""
        st.markdown(grid_html, unsafe_allow_html=True)

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
                        st.success("Compte créé avec succès ! Connectez-vous.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
