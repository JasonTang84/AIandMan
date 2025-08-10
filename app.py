"""
AIandMan - AI & Human Collaboration Tool
Refactored modular Streamlit application for AI image generation and review.
"""
import streamlit as st
from dotenv import load_dotenv
import os

# Import modular components
from state_manager import init_session_state, sync_selected_index
from background_tasks import check_background_tasks
from ui.styling import apply_page_config, apply_custom_css
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from ui.thumbnail_sidebar import render_thumbnail_sidebar

# Load environment variables
load_dotenv(override=True)

# Default password - can be overridden via environment variable
DEFAULT_PASSWORD = "aiandman2025"


@st.fragment(run_every=3)  # Auto-run every 3 seconds
def background_task_monitor():
    """Monitor background tasks and trigger rerun when completed"""
    if check_background_tasks():
        st.rerun()


def check_password():
    """Check if the user has entered the correct password"""
    # Get password from environment variable or use default
    app_password = os.getenv("APP_PASSWORD", DEFAULT_PASSWORD)
    
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, return True
    if st.session_state.authenticated:
        return True
    
    # Show login form
    st.title("🔐 AIandMan Authentication")
    st.markdown("Please enter the password to access the application.")
    
    with st.form("login_form"):
        password = st.text_input("Password", type="password", placeholder="Enter password...")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if password == app_password:
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    
    # Show password hint in development
    if os.getenv("STREAMLIT_ENV") == "development":
        st.info(f"💡 Development mode - Default password: `{DEFAULT_PASSWORD}`")
    
    return False


def main():
    """Main application entry point"""
    # Initialize page configuration
    apply_page_config()
    
    # Check authentication first
    if not check_password():
        return
    
    # Initialize session state
    init_session_state()
    
    # Sync selected index with selected item ID (handles UUID-based tracking)
    sync_selected_index()
    
    # Start background task monitoring (only if tasks exist)
    if st.session_state.background_futures:
        background_task_monitor()
    
    # Apply custom CSS styling
    apply_custom_css()
    
    # Add logout button in sidebar
    with st.sidebar:
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.rerun()
    
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


if __name__ == "__main__":
    main()