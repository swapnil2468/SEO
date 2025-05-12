import streamlit as st
import sys
import os

# Set page config once
st.set_page_config(page_title="SEO Optimization", layout="wide")

# Add project folders to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Project_1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Project_2'))

# Import project main files
import main1  # from Project_1/main1.py~
import main as project2_main  # from Project_2/main.py

# Initialize navigation state
if 'page' not in st.session_state:
    st.session_state.page = 'menu'
    
st.markdown("""
    <style>
    div.stButton > button {
        font-size: 20px;
        padding: 1em 2em;
    }
    </style>
""", unsafe_allow_html=True)

def main_menu():
    st.title("SEO Optimization")
    
    col1, col2 = st.columns([1, 1])
    col1.button("SEO Audit Runner", key="audit_btn", use_container_width=True, on_click=lambda: st.session_state.update(page='project1'))
    col2.button("Keywords Generator", key="keyword_btn", use_container_width=True, on_click=lambda: st.session_state.update(page='project2'))

# ONLY show sidebar back button **if NOT on menu page**
if st.session_state.page != 'menu':
    with st.sidebar:
        if st.button("Back to Main Menu"):
            st.session_state.page = 'menu'

# Route pages
if st.session_state.page == 'menu':
    main_menu()
elif st.session_state.page == 'project1':
    main1.main()
elif st.session_state.page == 'project2':
    project2_main.main()
