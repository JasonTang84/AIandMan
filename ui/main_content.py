"""
Main content area UI components.
"""
import streamlit as st
from state_manager import get_current_item, update_selected_index
from image_actions import reject_image, remove_current_image, create_download_button
from background_tasks import modify_image, generate_new_image


def render_main_content():
    """Render the complete sidebar with all input workflows"""
    # st.title("🎨 AI & Man(Collaboration Tool)")
    """Render the main content area"""
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    if not st.session_state.review_queue:
        render_empty_state()
    else:
        render_image_viewer()
    
    # Always show action controls
    st.divider()
    current_item = get_current_item()
    render_action_controls(current_item)
    
    # Add logs section below action controls
    render_logs_section()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_empty_state():
    """Render the empty state when no images are available"""
    st.info("📭 No images generated yet. Use the sidebar to generate or process images first!")
    st.markdown("### 🎨 How to get started:")
    st.markdown("1. **Text-to-Image**: Upload a text file with prompts in the left sidebar")
    st.markdown("2. **Image-to-Image**: Upload images for AI transformation")
    st.markdown("3. **Review**: Generated images will appear as thumbnails on the right")
    st.markdown("4. **Interact**: Click thumbnails to view, then accept/reject/modify")


def render_image_viewer():
    """Render the main image viewer and controls"""
    current_item = get_current_item()
    if not current_item:
        # No image selected
        st.info("📌 No image selected. Click the pin icon on a thumbnail in the right sidebar to select an image for viewing and editing.")
        return
    
    queue_length = len(st.session_state.review_queue)
    
    # Check if the selected image is still generating
    if current_item['image'] is None:
        render_generating_state(current_item)
        return
    
    # Header with navigation
    render_navigation_header(queue_length)
    
    st.divider()
    
    # Image display area
    render_image_display(current_item)
    
    # Note: Action controls are now rendered at the bottom of render_main_content()
    # to ensure they're always visible


def render_generating_state(current_item):
    """Render the state when an image is still generating"""
    st.info("🔄 This image is still being generated. Please wait or select another image.")
    
    # Show the prompt being generated
    if current_item['type'] == 'text_to_image':
        st.markdown("**🎨 Generating from prompt:**")
        with st.container():
            st.markdown(f"*\"{current_item['prompt']}\"*")
    else:
        st.markdown("**🖼️ Transforming image:**")
        if current_item.get('original_image'):
            st.image(current_item['original_image'], caption="Original", use_container_width=True)
        if current_item.get('modification_prompt'):
            st.markdown(f"**Transformation:** *{current_item['modification_prompt']}*")
    
    # Show spinner for generating state
    with st.spinner("Generating image..."):
        st.empty()


def render_navigation_header(queue_length):
    """Render the navigation header with prev/next buttons"""
    # Only show navigation if an image is selected
    if st.session_state.selected_image_index < 0:
        return
        
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.selected_image_index == 0):
            update_selected_index(st.session_state.selected_image_index - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>🎯 Image {st.session_state.selected_image_index + 1} of {queue_length}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("➡️ Next", disabled=st.session_state.selected_image_index >= queue_length - 1):
            update_selected_index(st.session_state.selected_image_index + 1)
            st.rerun()


def render_image_display(current_item):
    """Render the image display area"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if current_item['type'] == 'text_to_image':
            st.markdown("**🎨 Generated from prompt:**")
            with st.container():
                st.markdown(f"*\"{current_item['prompt']}\"*")
        else:
            st.markdown("**📸 Original Image:**")
            if current_item.get('original_image'):
                st.image(current_item['original_image'], caption="Original", use_container_width=True)
            if current_item.get('modification_prompt'):
                st.markdown(f"**Transformation:** *{current_item['modification_prompt']}*")
    
    with col2:
        st.markdown("**✨ Generated Result:**")
        st.image(current_item['image'], caption="Generated", use_container_width=True)


def render_action_controls(current_item):
    """Render the action controls for accept/reject/modify"""
    st.markdown("### 🎮 Review Actions")
    
    # Disable controls if no current item
    disabled = current_item is None or current_item.get('image') is None
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Use the download button function from image_actions
        create_download_button(current_item, disabled)
    
    with col2:
        if st.button("❌ Reject", use_container_width=True, help="Discard this image", disabled=disabled):
            reject_image()
    
    with col3:
        if st.button("🗑️ Remove", use_container_width=True, help="Remove from queue without saving", disabled=disabled):
            remove_current_image()
    
    # Second row for transformation controls
    modify_prompt = st.text_input(
        "🔄 Transform with new prompt:", 
        key="modify_prompt",
        placeholder="Enter transformation instructions...",
        disabled=False
    )
    
    # Third row for Create and Redo buttons
    col_create, col_redo = st.columns([1, 1])
    
    with col_create:
        if st.button("🎨 Create", use_container_width=True, help="Generate new image from prompt", disabled=False):
            if modify_prompt.strip():
                generate_new_image(modify_prompt)
    
    with col_redo:
        if st.button("🔄 Redo", use_container_width=True, help="Regenerate with new prompt", disabled=not modify_prompt.strip()):
            if modify_prompt.strip():
                if current_item:
                    modify_image(current_item, modify_prompt)
                else:
                    # Do nothing if there's no current image
                    pass


def render_logs_section():
    """Render the generation logs section"""
    if st.session_state.generation_logs:
        st.divider()
        st.header("📋 Generation Logs")
        
        # Show last 6 logs
        recent_logs = st.session_state.generation_logs[-6:]
        for log in recent_logs:
            st.text(log)
        
        if st.button("Clear Logs"):
            st.session_state.generation_logs = []
            st.rerun()
