# -*- coding: utf-8 -*-
"""
Board Game Library — card grid with filters and popup detail dialogs.
"""
import math
import streamlit as st
import pandas as pd


def _format_players(row):
    """Format player count string from min/max."""
    pmin = row.get('nb_joueurs_min')
    pmax = row.get('nb_joueur_max')
    if pd.isna(pmin) and pd.isna(pmax):
        return "?"
    pmin = int(pmin) if not pd.isna(pmin) else "?"
    pmax = int(pmax) if not pd.isna(pmax) else "?"
    if pmin == pmax:
        return str(pmin)
    return f"{pmin} – {pmax}"


def _format_duration(row):
    """Format duration string from min/max."""
    dmin = row.get('duree_min')
    dmax = row.get('duree_max')
    if pd.isna(dmin) and pd.isna(dmax):
        return "?"
    dmin = int(dmin) if not pd.isna(dmin) else None
    dmax = int(dmax) if not pd.isna(dmax) else None
    if dmin and dmax:
        if dmin == dmax:
            return f"{dmin} min"
        return f"{dmin} – {dmax} min"
    return f"{dmin or dmax} min"


def _format_age(row):
    """Format minimum age string."""
    age = row.get('age_min')
    if pd.isna(age):
        return "?"
    return f"{int(age)}+"


def _truncate(text, length=100):
    """Truncate text to a maximum length with ellipsis."""
    if not text or pd.isna(text):
        return ""
    text = str(text)
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + "…"


def _render_card_html(game, idx):
    """Generate HTML for a single game card."""
    name = str(game.get('nom', 'Sans nom'))
    img_url = game.get('lien_photo', '')
    if pd.isna(img_url) or not img_url:
        img_url = 'https://placehold.co/300x200/204a52/ffffff?text=No+Image'
    game_type = str(game.get('type', '')) if not pd.isna(game.get('type', '')) else ''
    desc = _truncate(game.get('description', ''), 110)

    badge_html = f'<span class="game-card-badge">{game_type}</span>' if game_type else ''

    return f'''
    <div class="game-card" id="game-card-{idx}">
        <div class="game-card-img-wrapper">
            <img class="game-card-img" src="{img_url}" alt="{name}" loading="lazy"
                 onerror="this.src='https://placehold.co/300x200/204a52/ffffff?text=No+Image'">
        </div>
        <div class="game-card-body">
            {badge_html}
            <h4 class="game-card-title">{name}</h4>
            <p class="game-card-desc">{desc}</p>
        </div>
    </div>
    '''


@st.dialog("📖 Détails du Jeu", width="large")
def _show_game_dialog():
    """Render game details inside a Streamlit dialog (popup modal with blurred backdrop)."""
    game = st.session_state.get('_dialog_game_data')
    if game is None:
        st.warning("Aucune donnée de jeu.")
        return

    name = str(game.get('nom', 'Sans nom'))
    img_url = game.get('lien_photo', '')
    if pd.isna(img_url) or not img_url:
        img_url = 'https://placehold.co/300x200/204a52/ffffff?text=No+Image'
    game_type = str(game.get('type', '')) if not pd.isna(game.get('type', '')) else 'Non spécifié'
    desc = str(game.get('description', '')) if not pd.isna(game.get('description', '')) else 'Aucune description disponible.'
    players = _format_players(game)
    duration = _format_duration(game)
    age = _format_age(game)
    is_extension = game.get('extension', '')
    ext_label = " · Extension" if (not pd.isna(is_extension) and str(is_extension).strip()) else ""

    # Header row: image + info
    col_img, col_info = st.columns([1, 2])

    with col_img:
        st.image(img_url, use_container_width=True)

    with col_info:
        st.markdown(f"### {name}")
        st.caption(f"🎯 {game_type}{ext_label}")

        # Stats row
        stat_cols = st.columns(3)
        with stat_cols[0]:
            st.metric("👥 Joueurs", players)
        with stat_cols[1]:
            st.metric("⏱️ Durée", duration)
        with stat_cols[2]:
            st.metric("🎂 Âge min.", age)

    # Description
    st.markdown("---")
    st.markdown("**📖 Description**")
    st.markdown(desc)

    # Bars where this game is available
    games_data = st.session_state.get('games_data')
    if games_data is not None and not games_data.empty:
        # Try exact match first, then fuzzy
        matching = games_data[games_data['game'].str.lower() == name.lower()]
        if matching.empty:
            matching = games_data[games_data['game'].str.lower().str.contains(name.lower(), na=False)]
        bar_names = sorted(matching['bar_name'].unique().tolist())
        if bar_names:
            st.markdown("---")
            st.markdown("**📍 Où trouver ce jeu ?**")
            with st.container(height=180):
                for b in bar_names:
                    st.markdown(f"🍷 {b}")


def render_game_library_tab(df_games):
    """Render the full Bibliothèque tab with filters and card grid."""
    if df_games is None or df_games.empty:
        st.warning("Aucune donnée de jeu disponible.")
        return

    st.subheader("📚 Bibliothèque de Jeux")
    st.caption(f"{len(df_games)} jeux disponibles dans notre catalogue")

    # ── Filters (stack on mobile via 2+2 layout) ─────────────
    col_search, col_type = st.columns(2)
    col_players, col_age = st.columns(2)

    with col_search:
        search_term = st.text_input(
            "🔍 Rechercher un jeu",
            placeholder="Tapez le nom d'un jeu…",
            key="lib_search"
        )

    with col_type:
        game_types = sorted(df_games['type'].dropna().unique().tolist()) if 'type' in df_games.columns else []
        selected_types = st.multiselect(
            "🎯 Type de jeu",
            game_types,
            placeholder="Tous les types",
            key="lib_type_filter"
        )

    with col_players:
        player_options = ["Tous", "1", "2", "3-4", "5-6", "7+"]
        selected_players = st.selectbox(
            "👥 Nombre de joueurs",
            player_options,
            key="lib_players_filter"
        )

    with col_age:
        age_options = ["Tous", "3+", "6+", "7+", "8+", "10+", "12+", "14+"]
        selected_age = st.selectbox(
            "🎂 Âge minimum",
            age_options,
            key="lib_age_filter"
        )

    # ── Apply Filters ────────────────────────────────────────
    filtered = df_games.copy()

    if search_term:
        filtered = filtered[filtered['nom'].str.contains(search_term, case=False, na=False)]

    if selected_types:
        filtered = filtered[filtered['type'].isin(selected_types)]

    if selected_players != "Tous":
        if selected_players == "1":
            filtered = filtered[filtered['nb_joueurs_min'] <= 1]
        elif selected_players == "2":
            filtered = filtered[
                (filtered['nb_joueurs_min'] <= 2) &
                (filtered['nb_joueur_max'] >= 2)
            ]
        elif selected_players == "3-4":
            filtered = filtered[
                (filtered['nb_joueurs_min'] <= 4) &
                (filtered['nb_joueur_max'] >= 3)
            ]
        elif selected_players == "5-6":
            filtered = filtered[
                (filtered['nb_joueurs_min'] <= 6) &
                (filtered['nb_joueur_max'] >= 5)
            ]
        elif selected_players == "7+":
            filtered = filtered[filtered['nb_joueur_max'] >= 7]

    if selected_age != "Tous":
        age_val = int(selected_age.replace('+', ''))
        filtered = filtered[filtered['age_min'] <= age_val]

    # ── Results Count ────────────────────────────────────────
    st.markdown(f"**{len(filtered)}** jeu(x) trouvé(s)")

    if filtered.empty:
        st.info("Aucun jeu ne correspond à vos critères. Essayez d'ajuster les filtres.")
        return

    # ── Pagination ───────────────────────────────────────────
    CARDS_PER_PAGE = 12
    total_pages = max(1, math.ceil(len(filtered) / CARDS_PER_PAGE))

    if 'lib_page' not in st.session_state:
        st.session_state.lib_page = 0

    # Reset page if filters changed
    if st.session_state.lib_page >= total_pages:
        st.session_state.lib_page = 0

    page = st.session_state.lib_page
    start_idx = page * CARDS_PER_PAGE
    end_idx = min(start_idx + CARDS_PER_PAGE, len(filtered))
    page_games = filtered.iloc[start_idx:end_idx]

    # ── Open dialog popup if triggered ───────────────────────
    if st.session_state.get('_open_game_dialog', False):
        st.session_state['_open_game_dialog'] = False
        _show_game_dialog()

    # ── Card Grid (render in rows of 3) ──────────────────────
    rows = [page_games.iloc[i:i+3] for i in range(0, len(page_games), 3)]

    for row_games in rows:
        cols = st.columns(3)
        for col_idx, (df_idx, game) in enumerate(row_games.iterrows()):
            with cols[col_idx]:
                # Card HTML
                card_html = _render_card_html(game, df_idx)
                st.markdown(card_html, unsafe_allow_html=True)

                # Detail button → opens popup dialog
                if st.button("🔍 Détails", key=f"btn_{df_idx}", use_container_width=True):
                    st.session_state['_dialog_game_data'] = game.to_dict()
                    st.session_state['_open_game_dialog'] = True
                    st.rerun()

    # ── Pagination Controls ──────────────────────────────────
    if total_pages > 1:
        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️", disabled=(page == 0), key="lib_prev", use_container_width=True):
                st.session_state.lib_page = max(0, page - 1)
                st.rerun()
        with col_info:
            st.markdown(
                f"<div style='text-align:center; padding-top:0.5rem;'>"
                f"<b>{page + 1}</b> / {total_pages}</div>",
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("➡️", disabled=(page >= total_pages - 1), key="lib_next", use_container_width=True):
                st.session_state.lib_page = min(total_pages - 1, page + 1)
                st.rerun()
