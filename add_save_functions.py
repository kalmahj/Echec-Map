#!/usr/bin/env python3
"""Add missing save functions"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where to insert (after load_forum_comments function)
insert_pos = None
for i, line in enumerate(lines):
    if line.strip() == 'return []' and i > 190 and i < 210:  # Likely the return from load_forum_comments
        # Check if previous lines contain load_forum_comments
        if any('def load_forum_comments' in lines[j] for j in range(max(0, i-10), i)):
            insert_pos = i + 1
            break

if insert_pos:
    # Lines to insert
    new_lines = [
        "\n",
        "def save_forum_comment(comment):\n",
        "    \"\"\"Save a forum comment to CSV and auto-commit\"\"\"\n",
        "    df = pd.DataFrame(st.session_state.forum_posts)\n",
        "    df.to_csv(FORUM_CSV_PATH, index=False, encoding='utf-8')\n",
        "    auto_commit_csv()\n",
        "\n",
        "def save_game_request(request):\n",
        "    \"\"\"Save a game request to CSV and auto-commit\"\"\"\n",
        "    df = pd.DataFrame(st.session_state.game_requests)\n",
        "    df.to_csv(GAME_REQUESTS_CSV_PATH, index=False, encoding='utf-8')\n",
        "    auto_commit_csv()\n",
        "\n"
    ]
    
    # Insert the lines
    lines[insert_pos:insert_pos] = new_lines
    
    # Write back
    with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Added save functions")
else:
    print("Could not find insertion point")
