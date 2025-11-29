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
import glob

# Configuration de la page
st.set_page_config(page_title="Bars à Jeux Paris", page_icon="🎮", layout="wide")

# Initialiser session state pour les posts du forum
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = []

# Initialiser session state pour les données de jeux
if 'games_data' not in st.session_state:
    st.session_state.games_data = pd.DataFrame(columns=['bar_name', 'game'])

# Chemin vers le fichier CSV des commentaires du forum
FORUM_CSV_PATH = os.path.join(os.path.dirname(__file__), 'forum_comments.csv')

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

# Fonction pour charger les jeux depuis les fichiers CSV
@st.cache_data
def load_games_from_csv():
    """Charge tous les jeux depuis les fichiers CSV du dossier Scraping Liste Jeux"""
    games_list = []
    csv_folder = os.path.join(os.path.dirname(__file__), 'Scraping Liste Jeux')
    
    if not os.path.exists(csv_folder):
        return pd.DataFrame(columns=['bar_name', 'game'])
    
    for csv_file, bar_name in BAR_CSV_MAPPING.items():
        csv_path = os.path.join(csv_folder, csv_file)
        if os.path.exists(csv_path):
            try:
                # Lire le CSV avec délimiteur point-virgule
                df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
                if 'Nom du jeu' in df.columns:
                    # Extraire les noms de jeux et les associer au bar
                    for game_name in df['Nom du jeu'].dropna().unique():
                        games_list.append({'bar_name': bar_name, 'game': str(game_name)})
            except Exception as e:
                st.warning(f"Erreur lors du chargement de {csv_file}: {e}")
    
    return pd.DataFrame(games_list)

# Fonction pour charger les commentaires du forum depuis le CSV
def load_forum_comments():
    """Charge les commentaires du forum depuis le fichier CSV s'il existe"""
    if os.path.exists(FORUM_CSV_PATH):
        try:
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except Exception as e:
            st.warning(f"Erreur lors du chargement des commentaires: {e}")
            return []
    return []

# Fonction pour sauvegarder un commentaire dans le CSV
def save_forum_comment(post):
    """Sauvegarde un nouveau commentaire dans le fichier CSV"""
    try:
        # Charger les commentaires existants ou créer un nouveau DataFrame
        if os.path.exists(FORUM_CSV_PATH):
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
        else:
            df = pd.DataFrame(columns=['username', 'bar', 'game', 'when', 'message', 'timestamp'])
        
        # Ajouter le nouveau commentaire
        new_row = pd.DataFrame([post])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Sauvegarder dans le CSV
        df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du commentaire: {e}")

# Charger les commentaires du forum au démarrage (une seule fois)
if len(st.session_state.forum_posts) == 0:
    st.session_state.forum_posts = load_forum_comments()

# Charger les jeux depuis les CSV (une seule fois)
if st.session_state.games_data.empty:
    st.session_state.games_data = load_games_from_csv()

# En-tête
st.title("🎮 Recherche de Bars à Jeux à Paris")
st.markdown("*Trouvez votre prochaine destination de jeu et connectez-vous avec d'autres joueurs !*")
st.markdown("---")

# Charger les données géographiques
@st.cache_data
def load_data():
    # Charger le fichier GeoJSON
    gdf_bar = gpd.read_file("liste_bar_OK.geojson")
    
    # Extraire les coordonnées depuis les colonnes existantes
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    
    # Nettoyer les données - supprimer les lignes sans nom ou sans coordonnées
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # Créer les onglets
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte et Recherche", "📋 Tous les Bars", "🎮 Gérer les Jeux", "💬 Forum Communautaire"])
    
    # ONGLET 1: Carte et Recherche
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("🔍 Trouver un Bar")
            
            # Recherche par nom
            search_name = st.text_input("Rechercher par nom :", placeholder="Entrez le nom du bar...")
            
            # Recherche par arrondissement
            arrondissements = sorted(gdf_bar['Arrondissement'].dropna().unique())
            selected_arrond = st.selectbox("Filtrer par arrondissement :", ["Tous"] + [str(a) for a in arrondissements])
            
            # Recherche par jeu (si des données de jeux existent)
            if not st.session_state.games_data.empty:
                all_games = sorted(st.session_state.games_data['game'].unique())
                selected_game = st.selectbox("Rechercher par jeu :", ["Tous les Jeux"] + all_games)
            else:
                selected_game = "Tous les Jeux"
                st.info("💡 Allez dans l'onglet 'Gérer les Jeux' pour ajouter des jeux aux bars !")
            
            # Appliquer les filtres
            filtered_gdf = gdf_bar.copy()
            
            if search_name:
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].str.contains(search_name, case=False, na=False)]
            
            if selected_arrond != "Tous":
                filtered_gdf = filtered_gdf[filtered_gdf['Arrondissement'].astype(str) == selected_arrond]
            
            if selected_game != "Tous les Jeux" and not st.session_state.games_data.empty:
                bars_with_game = st.session_state.games_data[st.session_state.games_data['game'] == selected_game]['bar_name'].unique()
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].isin(bars_with_game)]
                st.success(f"Trouvé {len(filtered_gdf)} bar(s) avec {selected_game}")
            
            st.info(f"Affichage de {len(filtered_gdf)} bar(s)")
            
            # Afficher la liste des bars filtrés
            if len(filtered_gdf) > 0:
                st.markdown("---")
                st.markdown("**Bars affichés :**")
                for idx, row in filtered_gdf.iterrows():
                    with st.expander(f"📍 {row['Nom']}"):
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
                        
                        # Afficher les jeux si disponibles
                        bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                        if not bar_games.empty:
                            games_list = ", ".join(bar_games['game'].tolist()[:10])  # Limiter à 10 jeux pour l'affichage
                            if len(bar_games) > 10:
                                games_list += f" ... (+{len(bar_games) - 10} autres)"
                            st.write(f"**🎮 Jeux :** {games_list}")
        
        with col1:
            st.subheader("🗺️ Carte des Bars à Jeux")
            if len(filtered_gdf) > 0:
                st.map(filtered_gdf[['lat', 'lon']])
            else:
                st.warning("Aucun bar trouvé avec les filtres sélectionnés.")
    
    # ONGLET 2: Tous les Bars
    with tab2:
        st.subheader("📋 Liste Complète des Bars à Jeux")
        
        # Préparer le DataFrame d'affichage
        display_df = gdf_bar[['Nom', 'Adresse', 'Arrondissement', 'Code postal', 'Métro', 'Téléphone', 'Site']].copy()
        
        # Ajouter une colonne pour les jeux
        display_df['Jeux'] = display_df['Nom'].apply(
            lambda name: ", ".join(st.session_state.games_data[st.session_state.games_data['bar_name'] == name]['game'].tolist()[:5])
            if name in st.session_state.games_data['bar_name'].values else ""
        )
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Option de téléchargement
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="bars_jeux_paris.csv",
            mime="text/csv",
        )
    
    # ONGLET 3: Gérer les Jeux
    with tab3:
        st.subheader("🎮 Gérer les Jeux par Bar")
        st.markdown("*Ajouter des jeux disponibles dans chaque bar*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Ajouter un Nouveau Jeu**")
            with st.form("add_game_form"):
                selected_bar = st.selectbox("Sélectionner un Bar :", gdf_bar['Nom'].sort_values().tolist())
                new_game = st.text_input("Nom du Jeu :", placeholder="ex: Échecs, Poker, Scrabble...")
                
                if st.form_submit_button("➕ Ajouter le Jeu"):
                    if new_game:
                        # Vérifier si la combinaison existe déjà
                        exists = ((st.session_state.games_data['bar_name'] == selected_bar) & 
                                 (st.session_state.games_data['game'] == new_game)).any()
                        
                        if not exists:
                            new_row = pd.DataFrame({'bar_name': [selected_bar], 'game': [new_game]})
                            st.session_state.games_data = pd.concat([st.session_state.games_data, new_row], ignore_index=True)
                            st.success(f"✅ Ajouté {new_game} à {selected_bar}")
                            st.rerun()
                        else:
                            st.warning("Ce jeu est déjà listé pour ce bar !")
                    else:
                        st.error("Veuillez entrer un nom de jeu !")
        
        with col2:
            st.markdown("**Jeux Actuels**")
            if not st.session_state.games_data.empty:
                # Grouper par bar
                for bar in st.session_state.games_data['bar_name'].unique():
                    games = st.session_state.games_data[st.session_state.games_data['bar_name'] == bar]['game'].tolist()
                    with st.expander(f"📍 {bar} ({len(games)} jeux)"):
                        for game in games:
                            col_a, col_b = st.columns([3, 1])
                            col_a.write(f"🎮 {game}")
                            if col_b.button("❌", key=f"del_{bar}_{game}"):
                                st.session_state.games_data = st.session_state.games_data[
                                    ~((st.session_state.games_data['bar_name'] == bar) & 
                                      (st.session_state.games_data['game'] == game))
                                ]
                                st.rerun()
            else:
                st.info("Aucun jeu ajouté pour le moment. Commencez à ajouter des jeux aux bars !")
    
    # ONGLET 4: Forum Communautaire
    with tab4:
        st.subheader("💬 Forum Communautaire")
        st.markdown("*Vous cherchez quelqu'un pour jouer ? Postez ici !*")
        
        # Section de création de post
        with st.form("new_post_form"):
            st.markdown("**Créer un Nouveau Post**")
            username = st.text_input("Votre Nom :", placeholder="Entrez votre nom")
            bar_choice = st.selectbox("Bar :", ["N'importe quel Bar"] + gdf_bar['Nom'].sort_values().tolist())
            
            if not st.session_state.games_data.empty:
                game_choice = st.selectbox("Jeu :", ["N'importe quel Jeu"] + sorted(st.session_state.games_data['game'].unique()))
            else:
                game_choice = st.text_input("Jeu :", placeholder="Entrez le nom du jeu")
            
            date_time = st.text_input("Quand :", placeholder="ex: Demain 19h, Ce samedi")
            message = st.text_area("Message :", placeholder="Salut ! Je cherche quelqu'un pour jouer aux échecs ce week-end...")
            
            submitted = st.form_submit_button("📤 Publier")
            
            if submitted:
                if username and message:
                    post = {
                        'username': username,
                        'bar': bar_choice,
                        'game': game_choice,
                        'when': date_time,
                        'message': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.forum_posts.insert(0, post)
                    save_forum_comment(post)  # Sauvegarder dans le CSV
                    st.success("✅ Post créé !")
                    st.rerun()
                else:
                    st.error("Veuillez remplir votre nom et votre message !")
        
        st.markdown("---")
        
        # Afficher les posts
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
                        if post['when']:
                            st.markdown(f"🕐 {post['when']}")
                        st.markdown(f"{post['message']}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{idx}"):
                            st.session_state.forum_posts.pop(idx)
                            # Resauvegarder tous les posts dans le CSV
                            try:
                                df = pd.DataFrame(st.session_state.forum_posts)
                                df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
                            except:
                                pass
                            st.rerun()
                    st.markdown("---")

except FileNotFoundError:
    st.error("⚠️ Impossible de charger le fichier liste_bar_OK.geojson. Assurez-vous que le chemin du fichier est correct.")
    st.info("Mettez à jour le chemin du fichier dans le code pour pointer vers votre fichier GeoJSON.")
except Exception as e:
    st.error(f"⚠️ Une erreur s'est produite : {str(e)}")
    st.info("Assurez-vous d'avoir les packages requis installés : streamlit, pandas, geopandas")

# Pied de page
st.markdown("---")
st.markdown("*Créé par Kalma et José bestie :)*")
