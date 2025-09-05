"""
Thumbnail sidebar UI component.
"""
import streamlit as st
import os
import time
import uuid
from PIL import Image
from dotenv import load_dotenv
from state_manager import remove_from_queue, add_log, remove_item_by_id, find_item_index_by_id
from ui.styling import render_background_task_status

# Load environment variables
load_dotenv()


def cancel_generating_image(item_id):
    """Cancel a generating image and remove it from the queue"""
    try:
        # Find the item index for logging
        item_index = find_item_index_by_id(item_id)
        if item_index == -1:
            st.error("Image not found in queue")
            return
        
        # Try to cancel the background task if it exists
        cancelled_task = False
        if st.session_state.background_futures:
            for i, future_info in enumerate(st.session_state.background_futures):
                if future_info.get('item_id') == item_id:
                    future = future_info['future']
                    if not future.done():
                        cancelled = future.cancel()
                        if cancelled:
                            cancelled_task = True
                            add_log(f"🛑 Cancelled background task for image {item_index + 1}")
                        else:
                            add_log(f"⚠️ Could not cancel background task for image {item_index + 1} (already running)")
                    
                    # Remove from background futures list
                    st.session_state.background_futures.pop(i)
                    break
        
        # Remove the image from the queue using simplified helper
        success = remove_item_by_id(item_id)
        
        if success:
            if cancelled_task:
                st.success(f"✅ Cancelled generation and removed image {item_index + 1}")
            else:
                st.success(f"✅ Removed image {item_index + 1} from queue")
            st.rerun()
        else:
            st.error("Failed to remove image from queue")
    except Exception as e:
        st.error(f"Error cancelling image: {str(e)}")


def remove_failed_image(item_id):
    """Remove a failed/timeout/cancelled image from the queue"""
    try:
        # Find the item index for logging
        item_index = find_item_index_by_id(item_id)
        if item_index == -1:
            st.error("Image not found in queue")
            return
            
        # Get status for logging
        item = st.session_state.review_queue[item_index]
        status = item.get('status', 'unknown')
        
        # Remove the image from the queue using simplified helper
        success = remove_item_by_id(item_id)
        
        if success:
            add_log(f"🗑️ Removed {status} image {item_index + 1}")
            st.success(f"✅ Removed {status} image from queue")
            st.rerun()
        else:
            st.error("Failed to remove image from queue")
    except Exception as e:
        st.error(f"Error removing image: {str(e)}")


def retry_timed_out_image(item_id):
    """Retry generation for a timed-out image"""
    try:
        # Import here to avoid circular import
        from background_tasks import thread_safe_log
        from ai_integration import AIImageGenerator
        from state_manager import update_item_by_id
        
        # Find the item by ID
        item = None
        for queue_item in st.session_state.review_queue:
            if queue_item.get('id') == item_id:
                item = queue_item
                break
        
        if not item:
            add_log("❌ Item not found for retry")
            return
        
        if item.get('status') != 'timeout':
            add_log("❌ Item is not in timeout status")
            return
        
        # Initialize AI generator
        try:
            ai_generator = AIImageGenerator()
        except Exception as e:
            add_log(f"❌ Failed to initialize AI Generator: {str(e)}")
            return
        
        # Reset item status to generating
        update_item_by_id(item_id, {'status': 'generating', 'image': None})
        
        # Get quality and resolution settings
        quality = getattr(st.session_state, 'image_quality', 'low')
        resolution = getattr(st.session_state, 'image_resolution', '1024x1024')
        
        # Submit new background task based on item type
        if item['type'] == 'text_to_image':
            prompt = item['prompt']
            future = st.session_state.executor.submit(
                ai_generator.generate_from_text, 
                prompt, 
                size=resolution, 
                quality=quality, 
                logger_callback=thread_safe_log
            )
            task_description = f"Retry: {prompt[:40]}..."
        else:  # image_to_image
            source_image = item.get('original_image') or item.get('source_image')
            modification_prompt = item.get('modification_prompt', '')
            
            if not source_image:
                add_log("❌ No source image available for retry")
                return
                
            future = st.session_state.executor.submit(
                ai_generator.modify_image, 
                source_image, 
                modification_prompt, 
                size=resolution, 
                quality=quality, 
                logger_callback=thread_safe_log
            )
            task_description = f"Retry transform: {modification_prompt[:40]}..."
        
        # Store future info for background checking
        st.session_state.background_futures.append({
            'future': future,
            'prompt': task_description,
            'item_id': item_id,
            'type': item['type']
        })
        
        add_log(f"🔄 Retrying generation: {task_description}")
        st.success("🔄 Retrying image generation...")
        st.rerun()
        
    except Exception as e:
        add_log(f"❌ Error retrying image: {str(e)}")
        st.error(f"Error retrying image: {str(e)}")


def render_thumbnail_sidebar():
    """Render the right sidebar with thumbnail gallery"""
    # Check environment variable flag for loading mock data
    load_mock_flag = os.getenv('LOAD_MOCK_IMAGES', 'false').lower() == 'true'
    if load_mock_flag:
        load_mock_images()
    
    with st.container():
        thumbnail_gallery()
        
        # Render background task status at the bottom of thumbnail sidebar
        render_background_task_status()


# Removed pil_to_base64 function - no longer needed with st.image approach


# Removed image_to_bytes function - no longer needed with st.image approach


def render_generating_thumbnail(i, item):
    """Render thumbnail for a generating image"""
    status = item.get('status', 'generating')
    item_id = item.get('id', f'legacy_{i}')  # Fallback for items without UUID
    
    with st.container():
        # Create columns for placeholder and button side by side
        col1, col2 = st.columns([3, 1])  # Placeholder gets 3/4 width, button gets 1/4
        
        with col1:
            if status == 'generating':
                # Create a placeholder box with animated processing text
                st.markdown("""
                <div style="
                    background-color: #f0f0f0;
                    border: 1px dashed #ccc;
                    height: 90px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 6px;
                    margin: 1px 0;
                ">
                    <div style="text-align: center; color: #666;">
                        <div class="processing-spinner" style="font-size: 16px;">🔄</div>
                        <div class="processing-dots" style="font-size: 10px;">Generating...</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif status in ['failed', 'timeout', 'cancelled']:
                # Create an error placeholder box
                error_icon = "⏰" if status == 'timeout' else "❌" if status == 'failed' else "🛑"
                error_text = "Timed Out" if status == 'timeout' else "Failed" if status == 'failed' else "Cancelled"
                
                st.markdown(f"""
                <div style="
                    background-color: #ffe6e6;
                    border: 1px solid #ff9999;
                    height: 90px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 6px;
                    margin: 1px 0;
                ">
                    <div style="text-align: center; color: #cc0000;">
                        <div style="font-size: 16px;">{error_icon}</div>
                        <div style="font-size: 10px;">{error_text}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Show truncated prompt as caption
            render_thumbnail_caption(item)
        
        with col2:
            # Minimal vertical spacing to align buttons with thumbnail
            st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
            
            # Add cancel/remove button based on status
            try:
                timestamp = int(item.get('timestamp', 0))
            except (ValueError, TypeError):
                timestamp = int(time.time())
            
            if status == 'generating':
                # Cancel button for generating images
                if st.button(
                    "❌", 
                    key=f"cancel_generating_{item_id}_{timestamp}", 
                    use_container_width=True,
                    help="Cancel this image generation"
                ):
                    cancel_generating_image(item_id)
            elif status == 'timeout':
                # For timeout status, show retry and remove buttons side by side
                col_retry, col_remove = st.columns(2)
                
                with col_retry:
                    if st.button(
                        "🔄", 
                        key=f"retry_timeout_{item_id}_{timestamp}", 
                        use_container_width=True,
                        help="Retry this image generation"
                    ):
                        retry_timed_out_image(item_id)
                
                with col_remove:
                    if st.button(
                        "🗑️", 
                        key=f"remove_timeout_{item_id}_{timestamp}", 
                        use_container_width=True,
                        help="Remove this timeout image"
                    ):
                        remove_failed_image(item_id)
            else:
                # Remove button for failed/cancelled images
                if st.button(
                    "🗑️", 
                    key=f"remove_failed_{item_id}_{timestamp}", 
                    use_container_width=True,
                    help=f"Remove this {status} image"
                ):
                    remove_failed_image(item_id)


def render_thumbnail_caption(item):
    """Render caption for thumbnail"""
    if item['type'] == 'text_to_image':
        # Shorter prompt preview for compact display
        prompt_preview = item['prompt'][:15] + "..." if len(item['prompt']) > 15 else item['prompt']
        st.caption(f"{prompt_preview}")
    else:
        # Just filename without icon for compact display
        filename = item.get('original_filename', 'Image')
        short_filename = filename[:12] + "..." if len(filename) > 12 else filename
        st.caption(f"{short_filename}")


def thumbnail_gallery():
    """Render the thumbnail gallery with statistics and clickable image grid"""
    st.markdown("### 🖼️ Image Gallery")
    
    if not st.session_state.review_queue:
        st.info("No images to display")
        return
    
    # Statistics at top
    render_gallery_stats()
    
    # Ultra-minimal divider
    st.markdown("<hr style='margin:0; padding:0; height:1px; border:none; background:#ccc;'>", unsafe_allow_html=True)
    
    # Only process images if there are any
    has_ready_images = any(item['image'] is not None for item in st.session_state.review_queue)
    
    if not has_ready_images:
        st.info("No ready images to display")
    else:
        # Display ready images using st.image with select buttons
        ready_items = []
        for i, item in enumerate(st.session_state.review_queue):
            if item['image'] is not None:
                ready_items.append((i, item))
        
        if ready_items:
            st.markdown("**Click pin icon to select an image:**")
            
            # Show which image is currently selected (only if one is actually selected)
            current_selected = st.session_state.get('selected_image_index', -1)
            if current_selected >= 0 and current_selected < len(st.session_state.review_queue):
                selected_item = st.session_state.review_queue[current_selected]
                if selected_item['image'] is not None:
                    # Find the display position of the selected image
                    display_position = None
                    for display_idx, (orig_idx, _) in enumerate(ready_items):
                        if orig_idx == current_selected:
                            display_position = display_idx + 1
                            break
                    if display_position:
                        st.markdown(f"🟢 **Selected: Image {display_position}**")
            
            # Display each ready image with select button
            for display_idx, (original_idx, item) in enumerate(ready_items):
                item_id = item.get('id', f'legacy_{original_idx}')
                timestamp = int(item.get('timestamp', time.time()))
                
                with st.container():
                    # Create columns for image and button side by side
                    col1, col2 = st.columns([3, 1])  # Image gets 3/4 width, button gets 1/4
                    
                    with col1:
                        # Display the image
                        st.image(
                            item['image'], 
                            width=90,  # Slightly smaller to fit with button
                            caption=None  # We'll add caption separately for better control
                        )
                        
                        # Add caption below image
                        if item['type'] == 'text_to_image':
                            prompt_preview = item['prompt'][:15] + "..." if len(item['prompt']) > 15 else item['prompt']
                            st.caption(f"{prompt_preview}")
                        else:
                            filename = item.get('original_filename', 'Image')
                            short_filename = filename[:12] + "..." if len(filename) > 12 else filename
                            st.caption(f"{short_filename}")
                    
                    with col2:
                        # Add some vertical spacing to center the button with image
                        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                        
                        # Add select button
                        is_selected = current_selected == original_idx
                        button_text = "✅" if is_selected else "📌"  # Pin icon for unselected, checkmark for selected
                        button_type = "secondary" if is_selected else "primary"
                        
                        if st.button(
                            button_text,
                            key=f"select_image_{item_id}_{timestamp}",
                            use_container_width=True,
                            type=button_type,
                            disabled=is_selected,
                            help="Select this image" if not is_selected else "Currently selected"
                        ):
                            # Update selection
                            st.session_state.selected_image_index = original_idx
                            st.session_state.selected_image_id = item_id
                            st.rerun()
                    
                    # Add small spacer between images
                    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    
    # Display generating images and failed/timeout/cancelled images separately (non-clickable)
    non_ready_items = []
    for i, item in enumerate(st.session_state.review_queue):
        status = item.get('status', 'generating' if item['image'] is None else 'ready')
        if item['image'] is None or status in ['generating', 'failed', 'timeout', 'cancelled']:
            non_ready_items.append((i, item))
    
    if non_ready_items:
        # Group by status for better organization
        generating_items = [(i, item) for i, item in non_ready_items if item.get('status', 'generating') == 'generating']
        failed_items = [(i, item) for i, item in non_ready_items if item.get('status') in ['failed', 'timeout', 'cancelled']]
        
        if generating_items:
            st.markdown("**Generating:**")
            for i, item in generating_items:
                render_generating_thumbnail(i, item)
        
        if failed_items:
            st.markdown("**Failed/Cancelled:**")
            for i, item in failed_items:
                render_generating_thumbnail(i, item)


def render_gallery_stats():
    """Render gallery statistics"""
    total_images = len(st.session_state.review_queue)
    
    # Count by actual status from review_queue items, not just image_states
    ready_count = 0
    generating_count = 0
    failed_count = 0
    timeout_count = 0
    cancelled_count = 0
    
    for item in st.session_state.review_queue:
        status = item.get('status', 'generating' if item['image'] is None else 'ready')
        if status == 'ready':
            ready_count += 1
        elif status == 'generating':
            generating_count += 1
        elif status == 'failed':
            failed_count += 1
        elif status == 'timeout':
            timeout_count += 1
        elif status == 'cancelled':
            cancelled_count += 1
    
    # Calculate total errors
    error_count = failed_count + timeout_count + cancelled_count
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total_images)
    with col2:
        st.metric("Ready", ready_count)
    with col3:
        st.metric("Generating", generating_count)
    with col4:
        if error_count > 0:
            st.metric("Errors", error_count, delta=f"F:{failed_count} T:{timeout_count} C:{cancelled_count}")
        else:
            st.metric("Errors", 0)


def load_mock_images():
    """
    MOCK FUNCTION FOR DEBUGGING - Load sample images for testing thumbnail sidebar
    
    This function is controlled by the LOAD_MOCK_IMAGES environment variable in .env
    Set LOAD_MOCK_IMAGES=true in your .env file to enable mock data
    Set LOAD_MOCK_IMAGES=false (or omit) to disable mock data
    
    To use this function:
    1. Place your test images in a 'mock_images' folder in the project root
    2. Or modify the image_paths list below with your own image paths
    3. Set LOAD_MOCK_IMAGES=true in your .env file to enable
    
    This function will automatically populate the thumbnail sidebar with test images
    """
    # Only load mock data if review_queue is empty (to avoid conflicts)
    if st.session_state.review_queue:
        return
    
    # Define mock image paths - MODIFY THESE PATHS TO YOUR TEST IMAGES
    mock_image_paths = [
        # Example paths - replace with your actual image paths
        "d:/Projects/MyProject2/AIandMan/mock_images/test1.jpg",
        "d:/Projects/MyProject2/AIandMan/mock_images/test2.png", 
        "d:/Projects/MyProject2/AIandMan/mock_images/test3.jpg",
        # Add more paths as needed
    ]
    
    # Alternative: Use a mock_images folder
    mock_folder = "d:/Projects/MyProject2/AIandMan/mock_images"
    if os.path.exists(mock_folder):
        # Get all image files from the mock folder
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        mock_image_paths = []
        for file in os.listdir(mock_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                mock_image_paths.append(os.path.join(mock_folder, file))
    
    # Load mock images into the review queue
    mock_items = []
    mock_states = []
    
    for i, image_path in enumerate(mock_image_paths):
        if os.path.exists(image_path):
            try:
                # Load image
                image = Image.open(image_path)
                
                # Create mock item
                mock_item = {
                    'id': str(uuid.uuid4()),  # Add UUID
                    'image': image,
                    'type': 'text_to_image',
                    'prompt': f"Mock image {i+1} from {os.path.basename(image_path)}",
                    'original_filename': os.path.basename(image_path),
                    'timestamp': time.time() + i,  # Use proper timestamp
                    'status': 'ready'
                }
                
                mock_items.append(mock_item)
                mock_states.append('ready')
                
            except Exception as e:
                st.error(f"Failed to load mock image {image_path}: {e}")
    
    # Add some generating placeholders for testing
    for i in range(2):  # Add 2 generating placeholders
        mock_item = {
            'id': str(uuid.uuid4()),  # Add UUID
            'image': None,
            'type': 'text_to_image', 
            'prompt': f"Mock generating image {i+1} - this is a longer prompt to test text truncation functionality",
            'timestamp': time.time() + 100 + i,  # Use proper timestamp
            'status': 'generating'
        }
        mock_items.append(mock_item)
        mock_states.append('generating')
    
    # Update session state
    if mock_items:
        st.session_state.review_queue = mock_items
        st.session_state.image_states = mock_states
        
        # Don't auto-select any image - let user choose manually
