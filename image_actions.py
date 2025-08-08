"""
Image actions for accept, reject, and other operations.
"""
import streamlit as st
import os
from state_manager import remove_from_queue, update_selected_index
from utils import ensure_output_folder


def accept_image(current_item):
    """Accept and save the current image"""
    try:
        ensure_output_folder(st.session_state.output_folder)
        
        # Generate filename
        timestamp = int(current_item['timestamp'])
        if current_item['type'] == 'text_to_image':
            filename = f"generated_{timestamp}.png"
        else:
            base_name = os.path.splitext(current_item['original_filename'])[0]
            filename = f"transformed_{base_name}_{timestamp}.png"
        
        # Save image
        filepath = os.path.join(st.session_state.output_folder, filename)
        current_item['image'].save(filepath)
        
        # Update stats and remove from queue
        st.session_state.stats['accepted'] += 1
        current_index = st.session_state.selected_image_index
        remove_from_queue(current_index)
        
        st.success(f"Image saved to {filepath}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error saving image: {str(e)}")


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
