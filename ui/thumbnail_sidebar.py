"""
Thumbnail sidebar UI component.
"""
import streamlit as st
import os
from PIL import Image


def render_thumbnail_sidebar():
    """Render the right sidebar with thumbnail gallery"""
    # MOCK FUNCTION - Comment this line to disable mock data
    load_mock_images()
    
    # Apply styling to the container
    st.markdown("""
    <style>
    div[data-testid="column"]:last-child > div {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        height: 100vh;
        overflow-y: auto;
    }
    
    /* Reduce spacing between elements in right sidebar */
    div[data-testid="column"]:last-child .stMarkdown {
        margin-bottom: 0.25rem !important;
    }
    
    div[data-testid="column"]:last-child .stMarkdown p {
        margin-bottom: 0.25rem !important;
    }
    
    /* Reduce spacing around images */
    div[data-testid="column"]:last-child .stImage {
        margin-bottom: 0.5rem !important;
    }
    
    /* Reduce button spacing */
    div[data-testid="column"]:last-child .stButton {
        margin-bottom: 0.25rem !important;
    }
    
    /* Make containers more compact */
    div[data-testid="column"]:last-child .stContainer > div {
        gap: 0.25rem !important;
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
        
        # Show status indicator (more compact)
        if status == 'generating':
            st.caption("🟡 Generating...")
        elif status == 'ready':
            st.caption("🟢 Ready")
        
        # Show truncated prompt
        render_thumbnail_caption(item)
        
        # Add minimal spacing between thumbnails (smaller gap)
        if i < len(st.session_state.review_queue) - 1:  # Don't add divider after last item
            st.markdown("<div style='margin: 5px 0; border-bottom: 1px solid #e0e0e0;'></div>", unsafe_allow_html=True)


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
        # Create a placeholder box with reduced margin
        st.markdown("""
        <div style="
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            margin: 2px 0;
        ">
            <div style="text-align: center; color: #666;">
                <div style="font-size: 20px;">🔄</div>
                <div style="font-size: 12px;">Processing...</div>
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


def load_mock_images():
    """
    MOCK FUNCTION FOR DEBUGGING - Load sample images for testing thumbnail sidebar
    
    To use this function:
    1. Place your test images in a 'mock_images' folder in the project root
    2. Or modify the image_paths list below with your own image paths
    3. Comment the function call in render_thumbnail_sidebar() to disable
    
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
                    'image': image,
                    'type': 'text_to_image',
                    'prompt': f"Mock image {i+1} from {os.path.basename(image_path)}",
                    'original_filename': os.path.basename(image_path),
                    'timestamp': f"Mock_{i+1}",
                }
                
                mock_items.append(mock_item)
                mock_states.append('ready')
                
            except Exception as e:
                st.error(f"Failed to load mock image {image_path}: {e}")
    
    # Add some generating placeholders for testing
    for i in range(2):  # Add 2 generating placeholders
        mock_item = {
            'image': None,
            'type': 'text_to_image', 
            'prompt': f"Mock generating image {i+1} - this is a longer prompt to test text truncation functionality",
            'timestamp': f"Mock_Gen_{i+1}",
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
