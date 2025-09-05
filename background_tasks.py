"""
Background task management for image generation.
Handles concurrent image generation and status checking.
"""
import streamlit as st
import time
import uuid
from typing import List
from PIL import Image
from concurrent.futures import TimeoutError
import threading

from ai_integration import AIImageGenerator
from state_manager import add_log, update_item_by_id

# Timeout settings
TASK_TIMEOUT = 90  # 1 minute and 30 seconds

# Thread-safe logging
_log_lock = threading.Lock()

def thread_safe_log(message: str):
    """Thread-safe logging function that can be called from executor threads"""
    with _log_lock:
        # Use a simple list append which is thread-safe for the log messages
        # The actual add_log call will happen in the main thread during check_background_tasks
        if not hasattr(st.session_state, 'pending_logs'):
            st.session_state.pending_logs = []
        st.session_state.pending_logs.append(message)


def check_background_tasks():
    """Simplified UUID-based task checking"""
    # Process any pending logs first
    if hasattr(st.session_state, 'pending_logs') and st.session_state.pending_logs:
        for log_message in st.session_state.pending_logs:
            add_log(log_message)
        st.session_state.pending_logs = []
    
    if not st.session_state.background_futures:
        return False
    
    completed_any = False
    remaining_futures = []
    
    for future_info in st.session_state.background_futures:
        future = future_info['future']
        current_time = time.time()
        item_id = future_info.get('item_id')
        
        if not item_id:
            # Skip futures without item_id (legacy)
            continue
        
        # Check if the task is actually running (not just queued)
        if future.running():
            # Task is actively running - start timing if not already started
            if 'processing_start_time' not in future_info:
                future_info['processing_start_time'] = current_time
                add_log(f"🏃 Started processing: {future_info['prompt'][:40]}...")
            
            processing_start_time = future_info['processing_start_time']
            elapsed_time = current_time - processing_start_time
            
            # Check if task has timed out (only while actually processing)
            if elapsed_time > TASK_TIMEOUT:
                prompt = future_info['prompt']
                
                # Cancel the future task
                future.cancel()
                add_log(f"⏰ Timeout ({TASK_TIMEOUT}s): {prompt[:40]}...")
                
                # Simple atomic update using helper function
                update_item_by_id(item_id, {'status': 'timeout'})
                completed_any = True
                continue
        
        if future.done():
            try:
                # Try to get result with a short timeout to avoid blocking
                image = future.result(timeout=0.1)
                prompt = future_info['prompt']
                
                if image:
                    # Simple atomic update using helper function
                    update_item_by_id(item_id, {'image': image, 'status': 'ready'})
                    st.session_state.stats['generated'] += 1
                    add_log(f"✅ Completed: {prompt[:40]}...")
                    completed_any = True
                else:
                    update_item_by_id(item_id, {'status': 'failed'})
                    add_log(f"❌ No image returned: {prompt[:40]}...")
                    completed_any = True
            except TimeoutError:
                # Task completed but result retrieval timed out
                prompt = future_info['prompt']
                add_log(f"⏰ Result timeout: {prompt[:40]}...")
                update_item_by_id(item_id, {'status': 'timeout'})
                completed_any = True
            except Exception as e:
                prompt = future_info['prompt']
                add_log(f"❌ Task failed: {prompt[:40]}... - {str(e)}")
                update_item_by_id(item_id, {'status': 'failed'})
                completed_any = True
        else:
            remaining_futures.append(future_info)
    
    st.session_state.background_futures = remaining_futures
    return completed_any


def generate_from_prompts(prompts: List[str]):
    """Generate images from text prompts in background (non-blocking)"""
    # Clear previous logs
    st.session_state.generation_logs = []
    
    # Immediate logging to confirm function is called
    add_log("🚀 FUNCTION CALLED: generate_from_prompts")
    add_log(f"🚀 STARTING GENERATION: {len(prompts)} prompts")
    
    try:
        add_log("🔧 Initializing AI Image Generator...")
        ai_generator = AIImageGenerator()
        add_log("✅ AI Image Generator initialized")
    except Exception as e:
        add_log(f"❌ Failed to initialize AI Generator: {str(e)}")
        return
    
    # Add placeholder items with 'generating' status
    for i, prompt in enumerate(prompts):
        item_id = str(uuid.uuid4())  # Generate unique ID
        add_log(f"📝 Adding prompt {i+1}: {prompt[:50]}...")
        st.session_state.review_queue.append({
            'id': item_id,  # Unique identifier
            'type': 'text_to_image',
            'image': None,  # Will be filled when generation completes
            'prompt': prompt,
            'timestamp': time.time(),
            'status': 'generating'
        })
        st.session_state.image_states.append('generating')
    
    add_log(f"📊 Queue now has {len(st.session_state.review_queue)} items")
    
    # Submit background tasks without waiting
    add_log(f"🔄 Starting background generation for {len(prompts)} tasks...")
    
    # Get quality and resolution settings from session state
    quality = getattr(st.session_state, 'image_quality', 'low')
    resolution = getattr(st.session_state, 'image_resolution', '1024x1024')
    
    # Get the items we just added (they have the UUIDs we need)
    recent_items = st.session_state.review_queue[-len(prompts):]
    
    for i, (prompt, item) in enumerate(zip(prompts, recent_items)):
        item_id = item['id']
        add_log(f"🎯 Submitting background task {i+1}: {prompt[:30]}...")
        future = st.session_state.executor.submit(ai_generator.generate_from_text, prompt, size=resolution, quality=quality, logger_callback=thread_safe_log)
        
        # Store future info for background checking (timeout timer starts only when processing begins)
        st.session_state.background_futures.append({
            'future': future,
            'prompt': prompt,
            'item_id': item_id,  # Use UUID instead of index
            'type': 'text_to_image'
        })
    
    add_log(f"✅ All {len(prompts)} tasks submitted to background executor")
    st.success(f"🎨 Started generating {len(prompts)} images in background! Images will appear in the gallery as they complete.")
    
    # Immediately rerun to show the placeholder images
    st.rerun()


def process_images(uploaded_files, modification_prompt: str):
    """Process uploaded images with AI transformation in background (non-blocking)"""
    try:
        ai_generator = AIImageGenerator()
    except Exception as e:
        st.error(f"Failed to initialize AI Generator: {str(e)}")
        return
    
    # Add placeholder items with 'generating' status
    item_ids = []  # Store item IDs for later reference
    for uploaded_file in uploaded_files:
        try:
            original_image = Image.open(uploaded_file)
            # Verify the image is valid by trying to load it
            original_image.load()
            # Convert to RGB if necessary for consistency
            if original_image.mode not in ('RGB', 'RGBA'):
                original_image = original_image.convert('RGB')
            
            item_id = str(uuid.uuid4())  # Generate unique ID
            item_ids.append(item_id)
            
            st.session_state.review_queue.append({
                'id': item_id,  # Unique identifier
                'type': 'image_to_image',
                'image': None,  # Will be filled when generation completes
                'original_image': original_image,
                'modification_prompt': modification_prompt,
                'original_filename': uploaded_file.name,
                'timestamp': time.time(),
                'status': 'generating'
            })
            st.session_state.image_states.append('generating')
        except Exception as e:
            st.error(f"❌ Error loading image {uploaded_file.name}: {str(e)}")
            continue
    
    add_log(f"🔄 Starting background processing for {len(uploaded_files)} images...")
    
    # Submit background tasks without waiting
    # Get quality and resolution settings from session state
    quality = getattr(st.session_state, 'image_quality', 'low')
    resolution = getattr(st.session_state, 'image_resolution', '1024x1024')
    
    for i, (uploaded_file, item_id) in enumerate(zip(uploaded_files, item_ids)):
        try:
            original_image = Image.open(uploaded_file)
            # Verify the image is valid
            original_image.load()
            # Convert to RGB if necessary
            if original_image.mode not in ('RGB', 'RGBA'):
                original_image = original_image.convert('RGB')
            
            future = st.session_state.executor.submit(ai_generator.modify_image, original_image, modification_prompt, size=resolution, quality=quality, logger_callback=thread_safe_log)
            
            # Store future info for background checking (timeout timer starts only when processing begins)
            st.session_state.background_futures.append({
                'future': future,
                'prompt': f"Transform {uploaded_file.name}",
                'item_id': item_id,  # Use UUID instead of index
                'type': 'image_to_image'
            })
            
            add_log(f"🎯 Submitted background task for: {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error processing image {uploaded_file.name}: {str(e)}")
            continue
    
    st.success(f"🖼️ Started processing {len(uploaded_files)} images in background! Results will appear as they complete.")
    st.rerun()


def generate_new_image(prompt: str):
    """Generate a new image from text prompt (non-blocking) - reuses existing functionality"""
    # Simply call the existing generate_from_prompts with a single prompt
    generate_from_prompts([prompt])
    
    # Don't auto-select the newly added image - let user choose manually


def modify_image(current_item, modify_prompt: str):
    """Request transformation of the current image (non-blocking)"""
    try:
        ai_generator = AIImageGenerator()
    except Exception as e:
        st.error(f"Failed to initialize AI Generator: {str(e)}")
        return
    
    # Create a placeholder for the new transformed image
    new_item = {
        **current_item,
        'id': str(uuid.uuid4()),  # Generate new unique ID
        'image': None,  # Will be filled when generation completes
        'timestamp': time.time(),
        'status': 'generating'
    }
    
    # Store the source image for display purposes (the image being modified)
    source_image = current_item.get('image') or current_item.get('original_image')
    new_item['source_image'] = source_image
    
    # Update prompts based on type
    if current_item['type'] == 'text_to_image':
        # For text-to-image modifications, we still want to show the source image on the left
        new_item['modification_prompt'] = modify_prompt
        task_description = f"Transform text-generated image: {modify_prompt[:40]}..."
    else:
        # Keep modification prompt for image transformation
        new_item['modification_prompt'] = modify_prompt
        task_description = f"Transform image: {modify_prompt[:40]}..."
    
    # Keep the original image in place and add the modified version as a new item
    # Add placeholder to queue (don't remove the original)
    st.session_state.review_queue.append(new_item)
    st.session_state.image_states.append('generating')
    
    # Get the new item ID for tracking
    new_item_id = new_item['id']
    
    # Get quality and resolution settings from session state
    quality = getattr(st.session_state, 'image_quality', 'low')
    resolution = getattr(st.session_state, 'image_resolution', '1024x1024')
    
    # When modifying an existing image, always use modify_image regardless of original type
    # Use the current image as the source for modification
    source_image = current_item.get('image') or current_item.get('original_image')
    if source_image:
        future = st.session_state.executor.submit(ai_generator.modify_image, source_image, modify_prompt, size=resolution, quality=quality, logger_callback=thread_safe_log)
    else:
        add_log(f"❌ Error: No source image available for modification")
        st.error("❌ Error: No source image available for modification")
        return
    
    # Store future info for background checking (timeout timer starts only when processing begins)
    st.session_state.background_futures.append({
        'future': future,
        'prompt': task_description,
        'item_id': new_item_id,  # Use UUID instead of index
        'type': current_item['type']
    })
    
    # Don't auto-select the newly added image - let user choose manually
    
    add_log(f"🔄 Started transformation (keeping original): {task_description}")
    st.success("🔄 Transformation started! The original image will be kept and the new image will appear when ready.")
    st.rerun()


def get_running_tasks_status():
    """Get status information about currently running background tasks"""
    if not st.session_state.background_futures:
        return "No active background tasks"
    
    current_time = time.time()
    status_lines = []
    
    for i, future_info in enumerate(st.session_state.background_futures):
        future = future_info['future']
        prompt = future_info['prompt'][:30]
        
        if future.running():
            # Task is actually processing
            if 'processing_start_time' in future_info:
                processing_start_time = future_info['processing_start_time']
                elapsed_time = current_time - processing_start_time
                remaining_time = max(0, TASK_TIMEOUT - elapsed_time)
                status_lines.append(f"Task {i+1}: {prompt}... (RUNNING: {elapsed_time:.1f}s elapsed, {remaining_time:.1f}s remaining)")
            else:
                status_lines.append(f"Task {i+1}: {prompt}... (RUNNING: just started)")
        elif future.done():
            status_lines.append(f"Task {i+1}: {prompt}... (COMPLETED)")
        else:
            status_lines.append(f"Task {i+1}: {prompt}... (QUEUED: waiting to start)")
    
    return "\n".join(status_lines)


def cancel_all_background_tasks():
    """Cancel all running background tasks"""
    if not st.session_state.background_futures:
        return False
    
    cancelled_count = 0
    for future_info in st.session_state.background_futures:
        future = future_info['future']
        if future.cancel():
            cancelled_count += 1
            queue_index = future_info['queue_index']
            if queue_index < len(st.session_state.image_states):
                st.session_state.image_states[queue_index] = 'cancelled'
            if queue_index < len(st.session_state.review_queue):
                st.session_state.review_queue[queue_index]['status'] = 'cancelled'
    
    st.session_state.background_futures = []
    add_log(f"🛑 Cancelled {cancelled_count} background tasks")
    return cancelled_count > 0
