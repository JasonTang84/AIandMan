"""
State management for the AIandMan application.
Handles all session state initialization and management.
"""
import streamlit as st
import os
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
        st.session_state.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)


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
    else:
        st.session_state.selected_image_index = 0


def remove_from_queue(index: int):
    """Remove an item from the review queue and adjust indices"""
    if 0 <= index < len(st.session_state.review_queue):
        st.session_state.review_queue.pop(index)
        if index < len(st.session_state.image_states):
            st.session_state.image_states.pop(index)
        
        # Adjust selected index if necessary
        if st.session_state.selected_image_index >= len(st.session_state.review_queue):
            st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
