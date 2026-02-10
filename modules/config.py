# -*- coding: utf-8 -*-
"""
Configuration constants and file paths for Echec-Map.
"""
import os

# --- Base directory (project root) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- File paths ---
LOGO_PATH = os.path.join(BASE_DIR, 'logo.png')
IMAGES_DIR = os.path.join(BASE_DIR, 'images_bars', 'images_bars')
USERS_JSON_PATH = os.path.join(BASE_DIR, 'users.json')
FORUM_CSV_PATH = os.path.join(BASE_DIR, 'forum_comments.csv')
GAME_REQUESTS_CSV_PATH = os.path.join(BASE_DIR, 'game_requests.csv')
ICONS_DIR = os.path.join(BASE_DIR, 'icone_joueurs', 'icone_joueurs')
INSULTS_PATH = os.path.join(BASE_DIR, 'liste_insultes.txt')
MENUS_DIR = os.path.join(BASE_DIR, 'Menus_bars')
CSV_GAMES_DIR = os.path.join(BASE_DIR, 'Scraping Liste Jeux')
THEME_CSS_PATH = os.path.join(BASE_DIR, 'theme.css')

# --- Mapping: CSV filename -> Bar display name ---
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

# --- Mapping: Bar name -> Menu PDF filename ---
BAR_MENU_MAPPING = {
    "Le dernier bar avant la fin du monde": "le_dernier_bar_avant_la_fin_du_monde.pdf",
    "Les grands gamins": "les_grands_gamins.pdf",
    "The good game": "the_good_game.pdf",
    "Le nid cocon ludique": "le_nid_cocon_ludique.pdf",
    "La Cabane": "la_cabane.pdf",
    "Loufoque": "loufoque.pdf",
    "Les Caves Alliées": "les_caves_alliees.pdf",
    "Le Chauve Qui Rit": "le_chauve_qui_rit.pdf",
    "Café Meisia": "cafe_meisia.pdf",
    "Les Mauvais Joueurs": "les_mauvais_joueurs.pdf",
    "Le Duchesse": "la_duchesse.pdf",
    "Au Bonheur des Jeux": "au_bonheur_des_jeux.pdf",
    "OberJeux": "oberjeux.pdf",
    "La revanche": "la_revanche.pdf",
    "Au Dé 12": "au_de_12.pdf",
    "Multivers (Ground control)": "multivers_ground_control.pdf",
    "Le 3bis": "le_3bis.pdf",
    "La Taverne De Fwinax": "la_taverne_de_fwinax.pdf",
    "Aux Dés Calés XVIIème": "aux_des_cales_XVII.pdf",
    "Aux dés calés XVIIIème": "aux_des_cales_XVIII.pdf",
    "Jovial": "jovial.pdf",
    "Café Jeux Natema": "cafe_jeux_natema.pdf",
}
