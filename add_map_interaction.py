#!/usr/bin/env python3
"""Enable map marker click to filter info box"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the st_folium call
old_code = '            st_folium(m, width="100%", height=600)'

new_code = '''            # Capture map interactions
            map_output = st_folium(m, width="100%", height=600, key="folium_map")
            
            # Update filter based on marker click
            if map_output and map_output.get("last_object_clicked"):
                clicked_lat = map_output["last_object_clicked"].get("lat")
                clicked_lng = map_output["last_object_clicked"].get("lng")
                
                if clicked_lat and clicked_lng:
                    # Find the bar that was clicked
                    for idx, row in map_data.iterrows():
                        if abs(row['lat'] - clicked_lat) < 0.0001 and abs(row['lon'] - clicked_lng) < 0.0001:
                            # Update the displayed info to show only this bar
                            filtered_gdf = map_data[map_data['Nom'] == row['Nom']]
                            has_filter = True
                            break'''

# Replace
content = content.replace(old_code, new_code)

# Write back
with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added map click interaction")
