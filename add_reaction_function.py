#!/usr/bin/env python3
"""Add missing add_reaction function"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where to insert (after save_game_request function)
insert_pos = None
for i, line in enumerate(lines):
    if 'def save_game_request' in line:
        # Find the end of this function (next blank line after the function)
        for j in range(i+1, min(i+20, len(lines))):
            if lines[j].strip() == '' and j > i + 5:
                insert_pos = j
                break
        break

if insert_pos:
    # Lines to insert
    new_lines = [
        "\n",
        "def add_reaction(post_idx, emoji):\n",
        "    \"\"\"Add a reaction to a post\"\"\"\n",
        "    if 'reactions' not in st.session_state.forum_posts[post_idx]:\n",
        "        st.session_state.forum_posts[post_idx]['reactions'] = {}\n",
        "    \n",
        "    reactions = st.session_state.forum_posts[post_idx]['reactions']\n",
        "    if isinstance(reactions, str):\n",
        "        try:\n",
        "            reactions = json.loads(reactions)\n",
        "        except:\n",
        "            reactions = {}\n",
        "    \n",
        "    reactions[emoji] = reactions.get(emoji, 0) + 1\n",
        "    st.session_state.forum_posts[post_idx]['reactions'] = json.dumps(reactions)\n",
        "    save_forum_comment(None)\n",
        "\n"
    ]
    
    # Insert the lines
    lines[insert_pos:insert_pos] = new_lines
    
    # Write back
    with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Added add_reaction function")
else:
    print("Could not find insertion point")
