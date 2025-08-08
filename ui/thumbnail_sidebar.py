"""
Thumbnail sidebar UI component.
"""
import streamlit as st


def render_thumbnail_sidebar():
    """Render the right sidebar with thumbnail gallery"""
    # Apply styling to the container
    st.markdown("""
    <style>
    div[data-testid="column"]:last-child > div {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        height: 100vh;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        thumbnail_gallery()


def thumbnail_gallery():
    """Render the thumbnail gallery with statistics and image grid"""
    st.markdown("### 🖼️ Image Gallery")
    
    if not st.session_state.review_queue:
        st.info("No images to display")
        return
    
    # Statistics at top
    render_gallery_stats()
    
    st.divider()
    
    # Thumbnail column
    st.markdown("**Click image to select:**")
    
    # Display thumbnails in a single column
    for i, item in enumerate(st.session_state.review_queue):
        render_thumbnail_item(i, item)


def render_gallery_stats():
    """Render gallery statistics"""
    total_images = len(st.session_state.review_queue)
    generating_count = st.session_state.image_states.count('generating')
    ready_count = st.session_state.image_states.count('ready')
    failed_count = st.session_state.image_states.count('failed')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total_images)
    with col2:
        st.metric("Ready", ready_count)
    with col3:
        st.metric("Generating", generating_count)


def render_thumbnail_item(i, item):
    """Render a single thumbnail item"""
    # Determine status and styling
    is_selected = i == st.session_state.selected_image_index
    status = st.session_state.image_states[i] if i < len(st.session_state.image_states) else 'ready'
    
    # Create container for each thumbnail
    with st.container():
        # Show selection indicator
        if is_selected:
            st.markdown("🟢 **Selected**")
        
        # Show thumbnail image or placeholder
        if item['image'] is not None:
            render_ready_thumbnail(i, item)
        else:
            render_generating_thumbnail(i, item)
        
        # Show status indicator
        if status == 'generating':
            st.markdown("🟡 Generating...")
        elif status == 'ready':
            st.markdown("🟢 Ready")
        
        # Show truncated prompt
        render_thumbnail_caption(item)
        
        # Add spacing between thumbnails
        if i < len(st.session_state.review_queue) - 1:  # Don't add divider after last item
            st.markdown("---")


def render_ready_thumbnail(i, item):
    """Render thumbnail for a ready image"""
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        # Display the image
        st.image(item['image'], use_container_width=True)
        
        # Invisible button that covers the image area
        if st.button(
            "📷",
            key=f"img_btn_{i}",
            help=f"Select this image",
            use_container_width=True
        ):
            st.session_state.selected_image_index = i
            st.rerun()


def render_generating_thumbnail(i, item):
    """Render thumbnail for a generating image"""
    with st.container():
        # Create a placeholder box
        st.markdown("""
        <div style="
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            margin: 10px 0;
        ">
            <div style="text-align: center; color: #666;">
                <div style="font-size: 24px;">🔄</div>
                <div style="font-size: 14px;">Processing...</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Still allow clicking on generating images
        if st.button(
            "🔄 View Progress",
            key=f"gen_btn_{i}",
            help=f"View generation progress",
            use_container_width=True
        ):
            st.session_state.selected_image_index = i
            st.rerun()


def render_thumbnail_caption(item):
    """Render caption for thumbnail"""
    if item['type'] == 'text_to_image':
        prompt_preview = item['prompt'][:40] + "..." if len(item['prompt']) > 40 else item['prompt']
        st.caption(f"📝 {prompt_preview}")
    else:
        st.caption(f"🖼️ {item.get('original_filename', 'Image')}")
