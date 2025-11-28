# -*- coding: utf-8 -*-
"""
Paris Game Bars Finder
A Streamlit app to find game bars in Paris and connect with other players
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime

# Page config
st.set_page_config(page_title="Paris Game Bars", page_icon="🎮", layout="wide")

# Initialize session state for forum posts
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = []

# Initialize session state for games data
if 'games_data' not in st.session_state:
    st.session_state.games_data = pd.DataFrame(columns=['bar_name', 'game'])

# Header
st.title("🎮 Paris Game Bars Finder")
st.markdown("*Find your next gaming spot and connect with players!*")
st.markdown("---")

# Load geodata
@st.cache_data
def load_data():
    gdf_bar = gpd.read_file(r"C:\Users\I84584\Downloads\bars.gpkg")
    
    # The geometry appears to be in a projected coordinate system (likely Lambert 93 for France)
    # Need to convert to WGS84 (EPSG:4326) for lat/lon
    if gdf_bar.crs is not None and gdf_bar.crs != "EPSG:4326":
        gdf_bar = gdf_bar.to_crs("EPSG:4326")
    
    # Source - https://stackoverflow.com/a
    # Posted by joris, modified by community. See post 'Timeline' for change history
    # Retrieved 2025-11-28, License - CC BY-SA 3.0
    gdf_bar['lon'] = gdf_bar.geometry.x
    gdf_bar['lat'] = gdf_bar.geometry.y
    
    return gdf_bar

try:
    gdf_bar = load_data()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map & Search", "📋 All Bars", "🎮 Manage Games", "💬 Community Forum"])
    
    # TAB 1: Map and Search
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.subheader("🔍 Find a Bar")
            
            # Search by name
            search_name = st.text_input("Search by name:", placeholder="Enter bar name...")
            
            # Search by arrondissement
            arrondissements = sorted(gdf_bar['arrondissement'].dropna().unique())
            selected_arrond = st.selectbox("Filter by arrondissement:", ["All"] + [str(a) for a in arrondissements])
            
            # Search by game (if games data exists)
            if not st.session_state.games_data.empty:
                all_games = sorted(st.session_state.games_data['game'].unique())
                selected_game = st.selectbox("Search by game:", ["All Games"] + all_games)
            else:
                selected_game = "All Games"
                st.info("💡 Go to 'Manage Games' tab to add games to bars!")
            
            # Apply filters
            filtered_gdf = gdf_bar.copy()
            
            if search_name:
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].str.contains(search_name, case=False, na=False)]
            
            if selected_arrond != "All":
                filtered_gdf = filtered_gdf[filtered_gdf['arrondissement'].astype(str) == selected_arrond]
            
            if selected_game != "All Games" and not st.session_state.games_data.empty:
                bars_with_game = st.session_state.games_data[st.session_state.games_data['game'] == selected_game]['bar_name'].unique()
                filtered_gdf = filtered_gdf[filtered_gdf['Nom'].isin(bars_with_game)]
                st.success(f"Found {len(filtered_gdf)} bar(s) with {selected_game}")
            
            st.info(f"Showing {len(filtered_gdf)} bar(s)")
            
            # Show filtered bars list
            if len(filtered_gdf) > 0:
                st.markdown("---")
                st.markdown("**Bars in view:**")
                for idx, row in filtered_gdf.iterrows():
                    with st.expander(f"📍 {row['Nom']}"):
                        st.write(f"**Address:** {row['Adresse']}")
                        st.write(f"**Arrondissement:** {row['arrondissement']}")
                        if pd.notna(row['codepostal']):
                            st.write(f"**Postal Code:** {row['codepostal']}")
                        if pd.notna(row['metro']):
                            st.write(f"**Metro:** {row['metro']}")
                        if pd.notna(row['telephone']):
                            st.write(f"**Phone:** {row['telephone']}")
                        if pd.notna(row['site_web']):
                            st.write(f"**Website:** {row['site_web']}")
                        
                        # Show games if available
                        bar_games = st.session_state.games_data[st.session_state.games_data['bar_name'] == row['Nom']]
                        if not bar_games.empty:
                            games_list = ", ".join(bar_games['game'].tolist())
                            st.write(f"**🎮 Games:** {games_list}")
        
        with col1:
            st.subheader("🗺️ Map of Game Bars")
            if len(filtered_gdf) > 0:
                st.map(filtered_gdf)
            else:
                st.warning("No bars found with the selected filters.")
    
    # TAB 2: All Bars
    with tab2:
        st.subheader("📋 Complete List of Game Bars")
        
        # Prepare display dataframe
        display_df = gdf_bar[['Nom', 'Adresse', 'arrondissement', 'codepostal', 'metro', 'telephone', 'site_web']].copy()
        
        # Add games column
        display_df['Games'] = display_df['Nom'].apply(
            lambda name: ", ".join(st.session_state.games_data[st.session_state.games_data['bar_name'] == name]['game'].tolist())
            if name in st.session_state.games_data['bar_name'].values else ""
        )
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download option
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="paris_game_bars.csv",
            mime="text/csv",
        )
    
    # TAB 3: Manage Games
    with tab4:
        st.subheader("🎮 Manage Games by Bar")
        st.markdown("*Add games available at each bar*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Add New Game**")
            with st.form("add_game_form"):
                selected_bar = st.selectbox("Select Bar:", gdf_bar['Nom'].sort_values().tolist())
                new_game = st.text_input("Game Name:", placeholder="e.g., Chess, Poker, Scrabble...")
                
                if st.form_submit_button("➕ Add Game"):
                    if new_game:
                        # Check if combination already exists
                        exists = ((st.session_state.games_data['bar_name'] == selected_bar) & 
                                 (st.session_state.games_data['game'] == new_game)).any()
                        
                        if not exists:
                            new_row = pd.DataFrame({'bar_name': [selected_bar], 'game': [new_game]})
                            st.session_state.games_data = pd.concat([st.session_state.games_data, new_row], ignore_index=True)
                            st.success(f"✅ Added {new_game} to {selected_bar}")
                            st.rerun()
                        else:
                            st.warning("This game is already listed for this bar!")
                    else:
                        st.error("Please enter a game name!")
        
        with col2:
            st.markdown("**Current Games**")
            if not st.session_state.games_data.empty:
                # Group by bar
                for bar in st.session_state.games_data['bar_name'].unique():
                    games = st.session_state.games_data[st.session_state.games_data['bar_name'] == bar]['game'].tolist()
                    with st.expander(f"📍 {bar} ({len(games)} games)"):
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
                st.info("No games added yet. Start adding games to bars!")
    
    # TAB 4: Community Forum
    with tab3:
        st.subheader("💬 Community Forum")
        st.markdown("*Looking for someone to play with? Post here!*")
        
        # Post creation section
        with st.form("new_post_form"):
            st.markdown("**Create a New Post**")
            username = st.text_input("Your Name:", placeholder="Enter your name")
            bar_choice = st.selectbox("Bar:", ["Any Bar"] + gdf_bar['Nom'].sort_values().tolist())
            
            if not st.session_state.games_data.empty:
                game_choice = st.selectbox("Game:", ["Any Game"] + sorted(st.session_state.games_data['game'].unique()))
            else:
                game_choice = st.text_input("Game:", placeholder="Enter game name")
            
            date_time = st.text_input("When:", placeholder="e.g., Tomorrow 7 PM, This Saturday")
            message = st.text_area("Message:", placeholder="Hey! Looking for someone to play chess this weekend...")
            
            submitted = st.form_submit_button("📤 Post")
            
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
                    st.success("✅ Post created!")
                    st.rerun()
                else:
                    st.error("Please fill in your name and message!")
        
        st.markdown("---")
        
        # Display posts
        st.markdown("**Recent Posts**")
        
        if len(st.session_state.forum_posts) == 0:
            st.info("No posts yet. Be the first to post!")
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
                            st.rerun()
                    st.markdown("---")

except FileNotFoundError:
    st.error("⚠️ Could not load the bars.gpkg file. Please make sure the file path is correct.")
    st.info("Update the file path in the code to point to your actual bars.gpkg file.")
except Exception as e:
    st.error(f"⚠️ An error occurred: {str(e)}")
    st.info("Make sure you have the required packages installed: streamlit, pandas, geopandas")

# Footer
st.markdown("---")
st.markdown("*Made by Kalma and José bestie :)*")