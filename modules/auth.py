# -*- coding: utf-8 -*-
"""
User authentication: load/save users, password hashing, login, registration, profanity filter.
"""
import os
import ast
import json
import glob
import hashlib
import streamlit as st

from modules.config import USERS_JSON_PATH, ICONS_DIR, INSULTS_PATH
from modules.git_ops import push_changes


def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_JSON_PATH):
        try:
            with open(USERS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_users(users_list):
    """Save users to JSON file and auto-commit."""
    try:
        with open(USERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(users_list, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        st.toast("💾 Utilisateurs sauvegardés", icon="✅")
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde users.json : {e}")
        return

    # Auto-commit users.json
    import subprocess
    repo_dir = os.path.dirname(USERS_JSON_PATH)
    try:
        subprocess.run(['git', 'config', 'user.email', 'app@echec-map.com'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Echec Map Bot'], cwd=repo_dir, capture_output=True)
        subprocess.run(['git', 'add', 'users.json'], cwd=repo_dir, capture_output=True)
        result = subprocess.run(['git', 'commit', '-m', 'Update users'], cwd=repo_dir, capture_output=True, text=True)
        if result.returncode == 0:
            push_changes()
        elif 'nothing to commit' not in result.stdout.lower():
            st.warning(f"⚠️ Git commit échoué : {result.stderr}")
    except Exception as e:
        st.warning(f"⚠️ Git auto-commit échoué : {e}")


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password, icon_path):
    """Create a new user. Returns (success, message, user_data)."""
    users = load_users()
    if any(u['username'] == username for u in users):
        return False, "Ce nom d'utilisateur existe déjà.", None

    new_user = {
        'username': username,
        'password': hash_password(password),
        'icon': icon_path,
        'role': 'user'
    }
    users.append(new_user)
    save_users(users)

    # Verify the write succeeded by re-reading
    verification = load_users()
    if not any(u['username'] == username for u in verification):
        return False, "⚠️ Erreur : l'utilisateur n'a pas été sauvegardé. Réessayez.", None

    return True, "Compte créé avec succès !", new_user


def verify_user(username, password):
    """Verify user credentials. Returns (success, user_data)."""
    users = load_users()

    # Check for hardcoded admin
    if username == "admin" and password == "admin123":
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
    """Get list of available avatar icon paths."""
    if os.path.exists(ICONS_DIR):
        return glob.glob(os.path.join(ICONS_DIR, "*.png"))
    return []


def load_insults():
    """Load list of insults from file."""
    if os.path.exists(INSULTS_PATH):
        try:
            with open(INSULTS_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                return ast.literal_eval(content)
        except:
            return []
    return []


def contains_profanity(text):
    """Check if text contains profanity."""
    if not text:
        return False
    insults = load_insults()
    text_lower = text.lower()
    for insult in insults:
        if insult.lower() in text_lower:
            return True
    return False
