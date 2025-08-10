"""
Image actions for accept, reject, and other operations.
"""
import streamlit as st
import os
import io
import time
from state_manager import remove_from_queue, update_selected_index


def get_image_download_data(current_item):
    """Convert image to bytes for download"""
    try:
        # Convert PIL Image to bytes
        img_buffer = io.BytesIO()
        current_item['image'].save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer.getvalue()
    except Exception as e:
        st.error(f"Error preparing image for download: {str(e)}")
        return None


def get_download_filename(current_item):
    """Generate appropriate filename for download"""
    try:
        timestamp = int(current_item.get('timestamp', 0))
    except (ValueError, TypeError):
        timestamp = int(time.time())
    
    if current_item['type'] == 'text_to_image':
        return f"generated_{timestamp}.png"
    else:
        base_name = os.path.splitext(current_item.get('original_filename', 'unknown'))[0]
        return f"transformed_{base_name}_{timestamp}.png"


def create_download_button(current_item, disabled=False):
    """Create a download button for the current image and handle the download logic"""
    if not current_item or current_item.get('image') is None:
        return st.button("✅ Accept", type="primary", use_container_width=True, disabled=True, help="No image available")
    
    image_data = get_image_download_data(current_item)
    filename = get_download_filename(current_item)
    
    if not image_data:
        return st.button("✅ Accept", type="primary", use_container_width=True, disabled=True, help="Error preparing image")
    
    # Create a unique key for this download based on item ID and timestamp
    item_id = current_item.get('id', 'unknown')
    try:
        timestamp = int(current_item.get('timestamp', 0))
    except (ValueError, TypeError):
        timestamp = int(time.time())
    
    download_key = f"download_{item_id}_{timestamp}"
    
    downloaded = st.download_button(
        label="✅ Accept & Download",
        data=image_data,
        file_name=filename,
        mime="image/png",
        type="primary",
        use_container_width=True,
        help="Download image to your computer",
        disabled=disabled,
        key=download_key
    )
    
    # Track if this image was downloaded and remove from queue
    if downloaded:
        download_session_key = f"downloaded_{download_key}"
        if download_session_key not in st.session_state:
            st.session_state[download_session_key] = True
            # Update stats and remove from queue
            st.session_state.stats['accepted'] += 1
            current_index = st.session_state.selected_image_index
            remove_from_queue(current_index)
            st.success(f"✅ Image downloaded: {filename}")
            st.rerun()
    
    return downloaded


def reject_image():
    """Reject the current image"""
    current_index = st.session_state.selected_image_index
    st.session_state.stats['rejected'] += 1
    remove_from_queue(current_index)
    
    st.success("Image rejected and removed from queue")
    st.rerun()


def remove_current_image():
    """Remove current image from queue without changing stats"""
    current_index = st.session_state.selected_image_index
    remove_from_queue(current_index)
    
    st.info("Image removed from queue")
    st.rerun()


def skip_current_image():
    """Move current image to back of queue"""
    if len(st.session_state.review_queue) > 1:
        current_index = st.session_state.selected_image_index
        current = st.session_state.review_queue.pop(current_index)
        current_state = st.session_state.image_states.pop(current_index) if current_index < len(st.session_state.image_states) else 'ready'
        
        st.session_state.review_queue.append(current)
        st.session_state.image_states.append(current_state)
        
        # Keep the same index to show the next image
        if st.session_state.selected_image_index >= len(st.session_state.review_queue):
            st.session_state.selected_image_index = 0
            
        st.info("Image moved to back of queue")
        st.rerun()
