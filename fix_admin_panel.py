#!/usr/bin/env python3
"""Fix admin panel display"""

# Read the file
with open('bar_a_jeux.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the admin panel code
old_code = """col_header1, col_header2 = st.columns([20, 1])
with col_header2:
    if st.button("🔧"):
        st.session_state.show_admin_panel = not st.session_state.show_admin_panel

    st.markdown("---")
    st.markdown("### 🔐 Accès Administrateur")
    if not st.session_state.admin_logged_in:
        admin_pw = st.text_input("Mot de passe:", type="password", key="admin_login")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Se connecter"):
                if admin_pw == "admin123":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect")
        with col2:
            if st.button("Annuler"):
                st.session_state.show_admin_panel = False
                st.rerun()
    else:
        st.success("✅ Connecté")
        if st.button("Se déconnecter"):
            st.session_state.admin_logged_in = False
            st.session_state.show_admin_panel = False
            st.rerun()
    st.markdown("---")"""

new_code = """col_header1, col_header2 = st.columns([20, 1])
with col_header2:
    if st.button("🔧"):
        st.session_state.show_admin_panel = not st.session_state.show_admin_panel

# Admin Panel - display in full width when activated
if st.session_state.show_admin_panel:
    st.markdown("---")
    st.markdown("### 🔐 Accès Administrateur")
    if not st.session_state.admin_logged_in:
        admin_pw = st.text_input("Mot de passe:", type="password", key="admin_login")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Se connecter"):
                if admin_pw == "admin123":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect")
        with col2:
            if st.button("Annuler"):
                st.session_state.show_admin_panel = False
                st.rerun()
    else:
        st.success("✅ Connecté")
        if st.button("Se déconnecter"):
            st.session_state.admin_logged_in = False
            st.session_state.show_admin_panel = False
            st.rerun()
    st.markdown("---")"""

# Replace
content = content.replace(old_code, new_code)

# Write back
with open('bar_a_jeux.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed admin panel display")
