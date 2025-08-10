"""
State management for the AIandMan application.
Handles all session state initialization and management.
"""
import streamlit as st
import os
import uuid
import concurrent.futures
from typing import Dict, List, Any


def init_session_state():
    """Initialize all session state variables"""
    if 'stats' not in st.session_state:
        st.session_state.stats = {'generated': 0, 'accepted': 0, 'rejected': 0}

    if 'review_queue' not in st.session_state:
        st.session_state.review_queue = []

    if 'processing_tasks' not in st.session_state:
        st.session_state.processing_tasks = []

    if 'background_futures' not in st.session_state:
        st.session_state.background_futures = []

    if 'selected_image_index' not in st.session_state:
        st.session_state.selected_image_index = 0

    if 'image_states' not in st.session_state:
        st.session_state.image_states = []  # Track state of each image

    if 'generation_logs' not in st.session_state:
        st.session_state.generation_logs = []

    if 'pending_logs' not in st.session_state:
        st.session_state.pending_logs = []

    if 'executor' not in st.session_state:
        st.session_state.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def find_item_by_id(item_id: str):
    """Find an item in the review queue by its UUID"""
    for item in st.session_state.review_queue:
        if item.get('id') == item_id:
            return item
    return None


def find_item_index_by_id(item_id: str) -> int:
    """Find the index of an item in the review queue by its UUID"""
    for i, item in enumerate(st.session_state.review_queue):
        if item.get('id') == item_id:
            return i
    return -1


def update_item_by_id(item_id: str, updates: dict) -> bool:
    """Update an item in the review queue by its UUID"""
    for item in st.session_state.review_queue:
        if item.get('id') == item_id:
            item.update(updates)
            return True
    return False


def remove_item_by_id(item_id: str) -> bool:
    """Remove an item from the review queue by its UUID"""
    for i, item in enumerate(st.session_state.review_queue):
        if item.get('id') == item_id:
            # Remove item and corresponding state
            st.session_state.review_queue.pop(i)
            if i < len(st.session_state.image_states):
                st.session_state.image_states.pop(i)
            
            # Update selection if needed
            if st.session_state.selected_image_index >= len(st.session_state.review_queue):
                st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
            
            # Clear selected item ID if it was the removed item
            if hasattr(st.session_state, 'selected_image_id') and st.session_state.selected_image_id == item_id:
                if st.session_state.review_queue and st.session_state.selected_image_index < len(st.session_state.review_queue):
                    current_item = st.session_state.review_queue[st.session_state.selected_image_index]
                    st.session_state.selected_image_id = current_item.get('id')
                else:
                    delattr(st.session_state, 'selected_image_id')
            
            return True
    return False


def sync_selected_index():
    """Sync selected index with selected item ID for robust tracking"""
    if not hasattr(st.session_state, 'selected_image_id') or not st.session_state.review_queue:
        return
    
    # Find the item with the selected ID
    selected_id = st.session_state.selected_image_id
    for i, item in enumerate(st.session_state.review_queue):
        if item.get('id') == selected_id:
            st.session_state.selected_image_index = i
            return
    
    # If selected item not found, reset to first item
    if st.session_state.review_queue:
        st.session_state.selected_image_index = 0
        st.session_state.selected_image_id = st.session_state.review_queue[0].get('id')


def add_log(message: str):
    """Add a log message to session state and print to console"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.generation_logs.append(log_entry)
    print(log_entry)
    # Keep only last 50 logs
    if len(st.session_state.generation_logs) > 50:
        st.session_state.generation_logs = st.session_state.generation_logs[-50:]


def get_current_item():
    """Get the currently selected item from the review queue"""
    if not st.session_state.review_queue:
        return None
    
    if st.session_state.selected_image_index >= len(st.session_state.review_queue):
        st.session_state.selected_image_index = 0
    
    return st.session_state.review_queue[st.session_state.selected_image_index]


def update_selected_index(new_index: int):
    """Safely update the selected image index"""
    if st.session_state.review_queue:
        st.session_state.selected_image_index = max(0, min(new_index, len(st.session_state.review_queue) - 1))
        # Update selected item ID to match new index
        if st.session_state.selected_image_index < len(st.session_state.review_queue):
            current_item = st.session_state.review_queue[st.session_state.selected_image_index]
            st.session_state.selected_image_id = current_item.get('id')
    else:
        st.session_state.selected_image_index = 0


def remove_from_queue(index: int):
    """Remove an item from the review queue and adjust indices (legacy function)"""
    if 0 <= index < len(st.session_state.review_queue):
        removed_item = st.session_state.review_queue.pop(index)
        if index < len(st.session_state.image_states):
            st.session_state.image_states.pop(index)
        
        # Clear selected item ID if the removed item was selected
        if hasattr(st.session_state, 'selected_image_id') and st.session_state.selected_image_id == removed_item.get('id'):
            delattr(st.session_state, 'selected_image_id')
        
        # Adjust selected index if necessary
        if st.session_state.selected_image_index >= len(st.session_state.review_queue):
            st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
        
        # Update selected item ID to match new index
        if st.session_state.review_queue and st.session_state.selected_image_index < len(st.session_state.review_queue):
            current_item = st.session_state.review_queue[st.session_state.selected_image_index]
            st.session_state.selected_image_id = current_item.get('id')
