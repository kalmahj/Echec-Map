# -*- coding: utf-8 -*-
"""
Forum operations: save, react, comment, delete, report posts; manage game requests.
"""
import json
import pandas as pd
import streamlit as st
from datetime import datetime

from modules.config import FORUM_CSV_PATH, GAME_REQUESTS_CSV_PATH
from modules.git_ops import auto_commit_csv


def save_forum_comment(comment):
    """Save all forum posts to CSV and auto-commit."""
    df = pd.DataFrame(st.session_state.forum_posts)
    df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()


def save_game_request(request):
    """Save all game requests to CSV and auto-commit."""
    df = pd.DataFrame(st.session_state.game_requests)
    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')
    auto_commit_csv()


def add_reaction(post_idx, emoji):
    """Add a reaction to a post."""
    if 'reactions' not in st.session_state.forum_posts[post_idx]:
        st.session_state.forum_posts[post_idx]['reactions'] = {}

    reactions = st.session_state.forum_posts[post_idx]['reactions']

    # Handle float/nan or string
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
    """Add a comment to a post."""
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
    """Delete a comment from a post."""
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
    """Delete a forum post."""
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts.pop(post_idx)
        save_forum_comment(None)


def report_forum_post(post_idx, reason):
    """Report a forum post."""
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts[post_idx]['reported'] = True
        st.session_state.forum_posts[post_idx]['report_reason'] = reason
        save_forum_comment(None)


def approve_game_request(req_idx):
    """Approve a game request."""
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'approved'
        save_game_request(None)


def reject_game_request(req_idx):
    """Reject a game request."""
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'rejected'
        save_game_request(None)
