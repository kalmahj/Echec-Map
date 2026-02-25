# -*- coding: utf-8 -*-
"""
Data loading: GeoJSON bars, game CSVs, forum comments, game requests.
"""
import os
import pandas as pd
import geopandas as gpd
import streamlit as st

from modules.config import BASE_DIR, CSV_GAMES_DIR, BAR_CSV_MAPPING, FORUM_CSV_PATH, GAME_REQUESTS_CSV_PATH, COMPLETE_GAMES_CSV_PATH
from modules.utils import detect_encoding


@st.cache_data
def load_data():
    """Load bar data from GeoJSON file."""
    geojson_path = os.path.join(BASE_DIR, "liste_bar_OK.geojson")
    gdf_bar = gpd.read_file(geojson_path)
    gdf_bar['lon'] = pd.to_numeric(gdf_bar['longitude'], errors='coerce')
    gdf_bar['lat'] = pd.to_numeric(gdf_bar['latitude'], errors='coerce')
    gdf_bar = gdf_bar[gdf_bar['Nom'].notna() & gdf_bar['lon'].notna() & gdf_bar['lat'].notna()]
    # Clean up names
    gdf_bar['Nom'] = gdf_bar['Nom'].astype(str)
    for artifact in ['arrow_right', 'arrow_down', 'arrow_left', 'arrow_up', '->']:
        gdf_bar['Nom'] = gdf_bar['Nom'].str.replace(artifact, '')
    gdf_bar['Nom'] = gdf_bar['Nom'].str.strip()
    return gdf_bar


@st.cache_data
def load_games_from_csv():
    """Load all game lists from CSV files in the scraping folder."""
    games_list = []

    if not os.path.exists(CSV_GAMES_DIR):
        return pd.DataFrame(columns=['bar_name', 'game'])

    for csv_file, bar_name in BAR_CSV_MAPPING.items():
        csv_path = os.path.join(CSV_GAMES_DIR, csv_file)
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
                        clean_game = str(game_name)
                        for artifact in ['arrow_right', 'arrow_down', 'arrow_left', 'arrow_up', '->']:
                            clean_game = clean_game.replace(artifact, '')
                        clean_game = clean_game.strip()
                        if clean_game:
                            games_list.append({'bar_name': bar_name, 'game': clean_game})
            except:
                pass

    return pd.DataFrame(games_list)


def load_forum_comments():
    """Load forum comments from CSV file."""
    if os.path.exists(FORUM_CSV_PATH):
        try:
            df = pd.read_csv(FORUM_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []


def load_game_requests():
    """Load game requests from CSV file."""
    if os.path.exists(GAME_REQUESTS_CSV_PATH):
        try:
            df = pd.read_csv(GAME_REQUESTS_CSV_PATH, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []
    return []


@st.cache_data
def load_complete_games():
    """Load the complete game catalogue from liste_jeux_complet.csv."""
    if not os.path.exists(COMPLETE_GAMES_CSV_PATH):
        return pd.DataFrame()

    try:
        df = pd.read_csv(COMPLETE_GAMES_CSV_PATH, sep=';', encoding='utf-8')
    except Exception:
        for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(COMPLETE_GAMES_CSV_PATH, sep=';', encoding=enc)
                break
            except Exception:
                continue
        else:
            return pd.DataFrame()

    # Ensure numeric columns
    for col in ['nb_joueurs_min', 'nb_joueur_max', 'age_min', 'duree_min', 'duree_max']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop duplicates by game name, keep first
    if 'nom' in df.columns:
        df = df.drop_duplicates(subset='nom', keep='first')

    # Drop the 'Unnamed: 5' column if present
    if 'Unnamed: 5' in df.columns:
        df = df.drop(columns=['Unnamed: 5'])

    return df.reset_index(drop=True)
