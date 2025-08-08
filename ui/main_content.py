"""
Main content area UI components.
"""
import streamlit as st
from state_manager import get_current_item, update_selected_index
from image_actions import accept_image, reject_image, remove_current_image
from background_tasks import modify_image


def render_main_content():
    """Render the main content area"""
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    if not st.session_state.review_queue:
        render_empty_state()
    else:
        render_image_viewer()
    
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
    
    st.divider()
    
    # Action buttons and controls
    render_action_controls(current_item)


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
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Accept", type="primary", use_container_width=True, help="Save image to output folder"):
            accept_image(current_item)
    
    with col2:
        if st.button("❌ Reject", use_container_width=True, help="Discard this image"):
            reject_image()
    
    with col3:
        modify_prompt = st.text_input(
            "🔄 Transform with new prompt:", 
            key="modify_prompt",
            placeholder="Enter transformation instructions..."
        )
        
        col3a, col3b = st.columns([1, 1])
        with col3a:
            if st.button("🔄 Redo", use_container_width=True, disabled=not modify_prompt.strip(), help="Regenerate with new prompt"):
                if modify_prompt.strip():
                    modify_image(current_item, modify_prompt)
        
        with col3b:
            if st.button("🗑️ Remove", use_container_width=True, help="Remove from queue without saving"):
                remove_current_image()
