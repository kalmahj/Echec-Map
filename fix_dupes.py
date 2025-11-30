#!/usr/bin/env python3
"""Remove duplicate session state initializations"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 89-94 (the duplicates)
del lines[88:94]

# Write the file back
with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Removed duplicate session state initializations")
