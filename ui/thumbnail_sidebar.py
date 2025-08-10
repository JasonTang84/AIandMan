"""
Thumbnail sidebar UI component.
"""
import streamlit as st
import os
import time
import uuid
from PIL import Image
from st_clickable_images import clickable_images
import base64
import io
from dotenv import load_dotenv
from state_manager import remove_from_queue, add_log, remove_item_by_id, find_item_index_by_id

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


def render_thumbnail_sidebar():
    """Render the right sidebar with thumbnail gallery"""
    # Check environment variable flag for loading mock data
    load_mock_flag = os.getenv('LOAD_MOCK_IMAGES', 'false').lower() == 'true'
    if load_mock_flag:
        load_mock_images()
    
    with st.container():
        thumbnail_gallery()


@st.cache_data
def pil_to_base64(image_bytes: bytes) -> str:
    """Convert PIL Image bytes to base64 string for st-clickable-images"""
    img_str = base64.b64encode(image_bytes).decode()
    return f"data:image/png;base64,{img_str}"


def image_to_bytes(image: Image.Image) -> bytes:
    """Convert PIL Image to bytes"""
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer.getvalue()


def render_generating_thumbnail(i, item):
    """Render thumbnail for a generating image"""
    status = item.get('status', 'generating')
    item_id = item.get('id', f'legacy_{i}')  # Fallback for items without UUID
    
    with st.container():
        if status == 'generating':
            # Create a placeholder box with animated processing text
            st.markdown("""
            <div style="
                background-color: #f0f0f0;
                border: 1px dashed #ccc;
                height: 100px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                margin: 1px 0;
                cursor: pointer;
            " onclick="this.style.backgroundColor='#e0e0e0';">
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
                height: 100px;
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
        else:
            # Remove button for failed/timeout/cancelled images
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
        # Longer prompt preview for better readability
        prompt_preview = item['prompt'][:50] + "..." if len(item['prompt']) > 50 else item['prompt']
        st.caption(f"{prompt_preview}")
    else:
        # Just filename without icon for compact display
        filename = item.get('original_filename', 'Image')
        short_filename = filename[:15] + "..." if len(filename) > 15 else filename
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
        # Prepare images for clickable_images only if needed
        ready_images = []
        image_indices = []
        captions = []
        
        for i, item in enumerate(st.session_state.review_queue):
            if item['image'] is not None:
                # Convert PIL Image to base64 string using cached function
                image_bytes = image_to_bytes(item['image'])
                image_b64 = pil_to_base64(image_bytes)
                ready_images.append(image_b64)
                image_indices.append(i)
                # Create caption
                if item['type'] == 'text_to_image':
                    prompt_preview = item['prompt'][:20] + "..." if len(item['prompt']) > 20 else item['prompt']
                    captions.append(f"{prompt_preview}")
                else:
                    filename = item.get('original_filename', 'Image')
                    short_filename = filename[:15] + "..." if len(filename) > 15 else filename
                    captions.append(f"{short_filename}")
        
        # Display clickable images for ready images
        if ready_images:
            st.markdown("**Click image to select:**")
            
            # Show which image is currently selected
            current_selected = st.session_state.get('selected_image_index', -1)
            if current_selected >= 0 and current_selected < len(st.session_state.review_queue):
                selected_item = st.session_state.review_queue[current_selected]
                if selected_item['image'] is not None:
                    # Find if the selected image is in our ready images list
                    for idx, orig_idx in enumerate(image_indices):
                        if orig_idx == current_selected:
                            st.markdown(f"🟢 **Selected: Image {idx + 1}**")
                            break
            
            clicked = clickable_images(
                ready_images,
                titles=captions,
                div_style={
                    "display": "flex", 
                    "justify-content": "center", 
                    "flex-wrap": "wrap",
                    "flex-direction": "column",
                    "align-items": "center",
                    "gap": "2px"
                },
                img_style={
                    "margin": "1px", 
                    "height": "100px", 
                    "width": "auto",
                    "max-width": "110px",
                    "cursor": "pointer", 
                    "border-radius": "4px",
                    "border": "2px solid transparent",
                    "transition": "border-color 0.2s ease"
                },
                key="thumbnail_gallery"
            )
            
            # Handle click - only rerun if selection actually changed
            if clicked >= 0 and clicked < len(image_indices):
                selected_index = image_indices[clicked]
                current_selected = st.session_state.get('selected_image_index', -1)
                if selected_index != current_selected:
                    st.session_state.selected_image_index = selected_index
                    # Also store the selected item ID for more robust tracking
                    if selected_index < len(st.session_state.review_queue):
                        selected_item = st.session_state.review_queue[selected_index]
                        st.session_state.selected_image_id = selected_item.get('id')
                    st.rerun()
    
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
        
        # Initialize selected index if not set
        if 'selected_image_index' not in st.session_state:
            st.session_state.selected_image_index = 0
