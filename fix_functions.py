# Script to add missing functions to bar_a_jeux.py

with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Change json.dumps(reactions) to json.dumps(reactions, ensure_ascii=False)
content = content.replace(
    "st.session_state.forum_posts[post_idx]['reactions'] = json.dumps(reactions)",
    "st.session_state.forum_posts[post_idx]['reactions'] = json.dumps(reactions, ensure_ascii=False)"
)

# Fix 2: Add missing functions after add_reaction
add_reaction_end = "    save_forum_comment(None)\n\n\n# Load data"
new_functions = """    save_forum_comment(None)

def add_comment_to_post(post_idx, author, text):
    \"\"\"Add a comment to a post\"\"\"
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
    \"\"\"Delete a comment from a post\"\"\"
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
    \"\"\"Delete a forum post\"\"\"
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts.pop(post_idx)
        save_forum_comment(None)

def report_forum_post(post_idx, reason):
    \"\"\"Report a forum post\"\"\"
    if 0 <= post_idx < len(st.session_state.forum_posts):
        st.session_state.forum_posts[post_idx]['reported'] = True
        st.session_state.forum_posts[post_idx]['report_reason'] = reason
        save_forum_comment(None)

def approve_game_request(req_idx):
    \"\"\"Approve a game request\"\"\"
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'approved'
        save_game_request(None)

def reject_game_request(req_idx):
    \"\"\"Reject a game request\"\"\"
    if 0 <= req_idx < len(st.session_state.game_requests):
        st.session_state.game_requests[req_idx]['status'] = 'rejected'
        save_game_request(None)


# Load data"""

content = content.replace(add_reaction_end, new_functions)

# Fix 3: Add proper emoji display in reactions
old_reactions_display = """                    # Reactions (Horizontal Layout)
                    reactions = post.get('reactions', '')
                    if reactions:
                        st.markdown(f"Réactions: {reactions}")"""

new_reactions_display = """                    # Reactions (Horizontal Layout)
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
                            st.markdown(f"**Réactions:** {reactions}")"""

content = content.replace(old_reactions_display, new_reactions_display)

# Write the fixed content
with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File fixed successfully!")
