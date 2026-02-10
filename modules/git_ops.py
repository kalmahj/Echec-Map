# -*- coding: utf-8 -*-
"""
Git operations: auto-commit CSV files and push changes.
"""
import os
import subprocess
import streamlit as st

from modules.config import BASE_DIR


def push_changes():
    """Push changes to remote repository."""
    try:
        subprocess.run(['git', 'push'], cwd=BASE_DIR, capture_output=True)
    except Exception as e:
        print(f"Push failed: {e}")


def auto_commit_csv():
    """Auto-commit CSV files (forum, game requests) and push."""
    # Configure local git identity
    try:
        subprocess.run(['git', 'config', 'user.email', 'app@echec-map.com'], cwd=BASE_DIR, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Echec Map Bot'], cwd=BASE_DIR, capture_output=True)
    except:
        pass

    if not os.path.exists(os.path.join(BASE_DIR, ".git")):
        st.error("⚠️ Git n'est pas initialisé dans ce dossier.")
        return

    try:
        result_add = subprocess.run(
            ['git', 'add', 'forum_comments.csv', 'game_requests.csv'],
            cwd=BASE_DIR, capture_output=True, text=True
        )
        if result_add.returncode != 0:
            st.error(f"Git Add Error: {result_add.stderr}")
            return

        result_commit = subprocess.run(
            ['git', 'commit', '-m', 'Auto-update CSV files'],
            cwd=BASE_DIR, capture_output=True, text=True
        )
        if result_commit.returncode != 0:
            if "nothing to commit" not in result_commit.stdout.lower():
                st.error(f"Git Commit Error: {result_commit.stderr}")
        else:
            st.toast("✅", icon="💾")
            push_changes()

    except FileNotFoundError:
        st.error("⚠️ Git n'est pas installé ou n'est pas dans le PATH.")
    except Exception as e:
        st.error(f"Auto-commit failed: {str(e)}")
