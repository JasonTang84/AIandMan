"""
UI styling and layout configuration.
"""
import streamlit as st


def apply_page_config():
    """Apply page configuration settings"""
    st.set_page_config(
        page_title="AIandMan", 
        page_icon="🎨", 
        layout="wide",
        initial_sidebar_state="expanded"
    )


def apply_custom_css():
    """Apply custom CSS styling for the application"""
    st.markdown("""
    <style>
    .css-1d391kg {
        width: 300px;
    }
    .css-1lcbmhc {
        max-width: 300px;
    }
    .st-emotion-cache-1legitb {
        max-width: 300px;
        min-width: 300px;
    }
    section[data-testid="stSidebar"] {
        width: 300px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 300px !important;
    }
    .main-content {
        padding: 0 20px;
    }
    .thumbnail-grid {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-top: 10px;
    }
    .thumbnail-item {
        position: relative;
        border: 3px solid transparent;
        border-radius: 12px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    .thumbnail-item:hover {
        border-color: #ff6b6b;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .thumbnail-item.selected {
        border-color: #4CAF50;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.6);
        transform: scale(1.02);
    }
    .thumbnail-item.generating {
        border-color: #ffa726;
        opacity: 0.7;
    }
    .thumbnail-status {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid white;
        z-index: 10;
    }
    .status-generating { background-color: #ffa726; }
    .status-ready { background-color: #4CAF50; }
    .status-reviewing { background-color: #2196F3; }
    .thumbnail-caption {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, rgba(0,0,0,0.8));
        color: white;
        padding: 8px;
        font-size: 12px;
    }
    
    /* Simple animated processing indicators */
    .processing-dots::after {
        content: "Processing";
        animation: dots 1.5s infinite;
    }
    
    @keyframes dots {
        0% { content: "Processing"; }
        25% { content: "Processing."; }
        50% { content: "Processing.."; }
        75% { content: "Processing..."; }
        100% { content: "Processing"; }
    }
    
    .processing-spinner {
        animation: spin 2s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)


def render_background_task_status():
    """Render background task status indicator"""
    if st.session_state.background_futures:
        active_tasks = len(st.session_state.background_futures)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<div style="color: #1f77b4;"><span class="processing-spinner">🔄</span> <span class="processing-dots">Generating {active_tasks} images in background</span></div>', unsafe_allow_html=True)
        with col2:
            if st.button("🔄 Refresh", help="Check for completed images"):
                st.rerun()
        
        # Show progress in the bottom
        generating_count = st.session_state.image_states.count('generating')
        if generating_count > 0:
            progress_container = st.container()
            with progress_container:
                completed_count = len([item for item in st.session_state.review_queue if item['image'] is not None])
                total_count = len(st.session_state.review_queue)
                if total_count > 0:
                    progress = completed_count / total_count
                    st.progress(progress, text=f"Generated {completed_count}/{total_count} images")
