"""
AIandMan - AI & Human Collaboration Tool
Refactored modular Streamlit application for AI image generation and review.
"""
import streamlit as st
from dotenv import load_dotenv

# Import modular components
from state_manager import init_session_state
from background_tasks import check_background_tasks
from ui.styling import apply_page_config, apply_custom_css, render_background_task_status
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from ui.thumbnail_sidebar import render_thumbnail_sidebar

# Load environment variables
load_dotenv(override=True)


@st.fragment(run_every=3)  # Auto-run every 3 seconds
def background_task_monitor():
    """Monitor background tasks and trigger rerun when completed"""
    if check_background_tasks():
        st.rerun()


def main():
    """Main application entry point"""
    # Initialize page configuration
    apply_page_config()
    
    # Initialize session state
    init_session_state()
    
    # Start background task monitoring (only if tasks exist)
    if st.session_state.background_futures:
        background_task_monitor()
    
    # Apply custom CSS styling
    apply_custom_css()
    
    # Render sidebar
    with st.sidebar:
        render_sidebar()
    
    # Main layout with two columns: main content (left), thumbnail sidebar (right)
    # Making right sidebar more compact
    col_main, col_right = st.columns([4, 0.8])
    
    with col_main:
        render_main_content()
    
    with col_right:
        render_thumbnail_sidebar()
    
    # Render background task status at the bottom
    render_background_task_status()


if __name__ == "__main__":
    main()