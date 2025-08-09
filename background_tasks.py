"""
Background task management for image generation.
Handles concurrent image generation and status checking.
"""
import streamlit as st
import time
from typing import List
from PIL import Image

from ai_integration import AIImageGenerator
from state_manager import add_log


def check_background_tasks():
    """Check and update completed background generation tasks"""
    if not st.session_state.background_futures:
        return False
    
    completed_any = False
    remaining_futures = []
    
    for future_info in st.session_state.background_futures:
        future = future_info['future']
        if future.done():
            try:
                image = future.result()
                queue_index = future_info['queue_index']
                prompt = future_info['prompt']
                
                if image and queue_index < len(st.session_state.review_queue):
                    # Update the existing item with the generated image
                    st.session_state.review_queue[queue_index]['image'] = image
                    st.session_state.review_queue[queue_index]['status'] = 'ready'
                    if queue_index < len(st.session_state.image_states):
                        st.session_state.image_states[queue_index] = 'ready'
                    st.session_state.stats['generated'] += 1
                    add_log(f"✅ Completed: {prompt[:40]}...")
                    completed_any = True
            except Exception as e:
                queue_index = future_info['queue_index']
                prompt = future_info['prompt']
                add_log(f"❌ Failed: {prompt[:40]}... - {str(e)}")
                # Mark as failed
                if queue_index < len(st.session_state.image_states):
                    st.session_state.image_states[queue_index] = 'failed'
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
        add_log(f"📝 Adding prompt {i+1}: {prompt[:50]}...")
        st.session_state.review_queue.append({
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
    
    for i, prompt in enumerate(prompts):
        queue_index = len(st.session_state.review_queue) - len(prompts) + i
        add_log(f"🎯 Submitting background task {i+1}: {prompt[:30]}...")
        future = st.session_state.executor.submit(ai_generator.generate_from_text, prompt)
        
        # Store future info for background checking
        st.session_state.background_futures.append({
            'future': future,
            'prompt': prompt,
            'queue_index': queue_index,
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
    for uploaded_file in uploaded_files:
        try:
            original_image = Image.open(uploaded_file)
            # Verify the image is valid by trying to load it
            original_image.load()
            # Convert to RGB if necessary for consistency
            if original_image.mode not in ('RGB', 'RGBA'):
                original_image = original_image.convert('RGB')
                
            st.session_state.review_queue.append({
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
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            queue_index = len(st.session_state.review_queue) - len(uploaded_files) + i
            original_image = Image.open(uploaded_file)
            # Verify the image is valid
            original_image.load()
            # Convert to RGB if necessary
            if original_image.mode not in ('RGB', 'RGBA'):
                original_image = original_image.convert('RGB')
            
            future = st.session_state.executor.submit(ai_generator.modify_image, original_image, modification_prompt)
            
            # Store future info for background checking
            st.session_state.background_futures.append({
                'future': future,
                'prompt': f"Transform {uploaded_file.name}",
                'queue_index': queue_index,
                'type': 'image_to_image'
            })
            
            add_log(f"🎯 Submitted background task for: {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error processing image {uploaded_file.name}: {str(e)}")
            continue
    
    st.success(f"🖼️ Started processing {len(uploaded_files)} images in background! Results will appear as they complete.")
    st.rerun()


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
        'image': None,  # Will be filled when generation completes
        'timestamp': time.time(),
        'status': 'generating'
    }
    
    # Update prompts based on type
    if current_item['type'] == 'text_to_image':
        # Combine original prompt with transformation
        new_item['prompt'] = f"{current_item['prompt']} {modify_prompt}"
        task_description = f"Transform text: {new_item['prompt'][:40]}..."
    else:
        # Keep modification prompt for image transformation
        new_item['modification_prompt'] = modify_prompt
        task_description = f"Transform image: {modify_prompt[:40]}..."
    
    # Add placeholder to queue
    st.session_state.review_queue.append(new_item)
    st.session_state.image_states.append('generating')
    
    # Submit background task
    queue_index = len(st.session_state.review_queue) - 1
    
    if current_item['type'] == 'text_to_image':
        future = st.session_state.executor.submit(ai_generator.generate_from_text, new_item['prompt'])
    else:
        future = st.session_state.executor.submit(ai_generator.modify_image, current_item['original_image'], modify_prompt)
    
    # Store future info for background checking
    st.session_state.background_futures.append({
        'future': future,
        'prompt': task_description,
        'queue_index': queue_index,
        'type': current_item['type']
    })
    
    # Remove current image from queue
    current_index = st.session_state.selected_image_index
    st.session_state.review_queue.pop(current_index)
    if current_index < len(st.session_state.image_states):
        st.session_state.image_states.pop(current_index)
    
    # Select the newly added image (now at the end)
    st.session_state.selected_image_index = len(st.session_state.review_queue) - 1
    
    add_log(f"🔄 Started transformation: {task_description}")
    st.success("🔄 Transformation started! The new image will appear when ready.")
    st.rerun()
