#!/usr/bin/env python3
"""Fix session state initialization in bar_a_jeux.py"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line "if 'show_games' not in st.session_state:"
# and insert the missing session state initializations after the matching block
for i, line in enumerate(lines):
    if line.strip() == "if 'show_games' not in st.session_state:":
        # Found it, now insert after the next line (the assignment)
        insert_pos = i + 2  # After "    st.session_state.show_games = {}"
        
        # Lines to insert  
        new_lines = [
            "if 'forum_posts' not in st.session_state:\n",
            "    st.session_state.forum_posts = []\n",
            "if 'game_requests' not in st.session_state:\n",
            "    st.session_state.game_requests = []\n",
            "if 'games_data' not in st.session_state:\n",
            "    st.session_state.games_data = pd.DataFrame()\n"
        ]
        
        # Insert the lines
        lines[insert_pos:insert_pos] = new_lines
        break

# Write the file back
with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed session state initialization")
