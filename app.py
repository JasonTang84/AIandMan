import streamlit as st
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import concurrent.futures
from PIL import Image
import io
import time

from ai_integration import AIImageGenerator
from utils import parse_text_prompts, ensure_output_folder

# Load environment variables
load_dotenv()

# Initialize session state
if 'stats' not in st.session_state:
    st.session_state.stats = {'generated': 0, 'accepted': 0, 'rejected': 0}

if 'review_queue' not in st.session_state:
    st.session_state.review_queue = []

if 'processing_tasks' not in st.session_state:
    st.session_state.processing_tasks = []

if 'output_folder' not in st.session_state:
    st.session_state.output_folder = os.getenv('OUTPUT_FOLDER', './output')

if 'selected_image_index' not in st.session_state:
    st.session_state.selected_image_index = 0

if 'image_states' not in st.session_state:
    st.session_state.image_states = []  # Track state of each image: 'generating', 'ready', 'reviewing'

if 'generation_logs' not in st.session_state:
    st.session_state.generation_logs = []

def add_log(message):
    """Add a log message to session state and print to console"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.generation_logs.append(log_entry)
    print(log_entry)
    # Keep only last 50 logs
    if len(st.session_state.generation_logs) > 50:
        st.session_state.generation_logs = st.session_state.generation_logs[-50:]

def main():
    st.set_page_config(
        page_title="AIandMan", 
        page_icon="🎨", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configure layout with CSS for three-column layout
    st.markdown("""
    <style>
    .css-1d391kg {
        width: 400px;
    }
    .css-1lcbmhc {
        max-width: 400px;
    }
    .st-emotion-cache-1legitb {
        max-width: 400px;
        min-width: 400px;
    }
    section[data-testid="stSidebar"] {
        width: 400px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 400px !important;
    }
    .main-content {
        padding: 0 20px;
    }
    .right-sidebar {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        height: 100vh;
        overflow-y: auto;
    }
    .thumbnail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .thumbnail-item {
        position: relative;
        border: 2px solid transparent;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .thumbnail-item:hover {
        border-color: #ff6b6b;
        transform: scale(1.05);
    }
    .thumbnail-item.selected {
        border-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
    }
    .thumbnail-item.generating {
        border-color: #ffa726;
        opacity: 0.7;
    }
    .thumbnail-status {
        position: absolute;
        top: 5px;
        right: 5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    .status-generating { background-color: #ffa726; }
    .status-ready { background-color: #4CAF50; }
    .status-reviewing { background-color: #2196F3; }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for input workflows
    with st.sidebar:
        st.title("🎨 AIandMan")
        st.subheader("AI & Human Collaboration Tool")
        
        # Configuration section
        st.header("Configuration")
        st.session_state.output_folder = st.text_input(
            "Output Folder", 
            value=st.session_state.output_folder,
            help="Folder where accepted images will be saved"
        )
        
        # Statistics section
        st.header("Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Generated", st.session_state.stats['generated'])
        with col2:
            st.metric("Accepted", st.session_state.stats['accepted'])
        with col3:
            st.metric("Rejected", st.session_state.stats['rejected'])
        
        st.divider()
        
        # Text-to-Image workflow
        st.header("📝 Text-to-Image")
        text_to_image_interface()
        
        st.divider()
        
        # Image to Image workflow
        st.header("🖼️ Image to Image")
        image_modification_interface()
        
        # Generation Logs section
        if st.session_state.generation_logs:
            st.divider()
            st.header("📋 Generation Logs")
            
            # Show last 10 logs
            recent_logs = st.session_state.generation_logs[-10:]
            for log in recent_logs:
                st.text(log)
            
            if st.button("Clear Logs"):
                st.session_state.generation_logs = []
                st.rerun()
    
    # Main layout with three columns: sidebar (left), main content (center), thumbnail sidebar (right)
    col_main, col_right = st.columns([3, 1])
    
    with col_main:
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        # Main area for image display and interactions
        main_content_area()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
        # Right sidebar for thumbnails
        thumbnail_sidebar()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Background task status
    if st.session_state.processing_tasks:
        st.info(f"🔄 Processing {len(st.session_state.processing_tasks)} tasks in background...")

def text_to_image_interface():
    st.write("Upload a text file with prompts separated by semicolons (`;`)")
    
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['txt'],
        key="text_file",
        help="Limit 200MB per file • TXT"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        prompts = parse_text_prompts(content)
        
        st.success(f"Found {len(prompts)} prompts")
        
        if st.button("Generate Images", type="primary", use_container_width=True):
            generate_from_prompts(prompts)

def image_modification_interface():
    st.write("Upload images for AI-powered transformation")
    
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key="image_files"
    )
    
    modification_prompt = st.text_area(
        "Transformation Instructions",
        placeholder="e.g., 'Make it more colorful'",
        height=80
    )
    
    if uploaded_files and st.button("Transform Images", type="primary", use_container_width=True):
        process_images(uploaded_files, modification_prompt)

def main_content_area():
    """Main content area showing the selected image and controls"""
    if not st.session_state.review_queue:
        st.info("📭 No images generated yet. Use the sidebar to generate or process images first!")
        st.markdown("### 🎨 How to get started:")
        st.markdown("1. **Text-to-Image**: Upload a text file with prompts in the left sidebar")
        st.markdown("2. **Image-to-Image**: Upload images for AI transformation")
        st.markdown("3. **Review**: Generated images will appear as thumbnails on the right")
        st.markdown("4. **Interact**: Click thumbnails to view, then accept/reject/modify")
        return
    
    # Get the currently selected image
    if st.session_state.selected_image_index >= len(st.session_state.review_queue):
        st.session_state.selected_image_index = 0
    
    current_item = st.session_state.review_queue[st.session_state.selected_image_index]
    queue_length = len(st.session_state.review_queue)
    
    # Check if the selected image is still generating
    if current_item['image'] is None:
        st.warning("🔄 This image is still being generated. Please wait or select another image.")
        return
    
    # Header with navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.selected_image_index == 0):
            st.session_state.selected_image_index = max(0, st.session_state.selected_image_index - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>🎯 Image {st.session_state.selected_image_index + 1} of {queue_length}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("➡️ Next", disabled=st.session_state.selected_image_index >= queue_length - 1):
            st.session_state.selected_image_index = min(queue_length - 1, st.session_state.selected_image_index + 1)
            st.rerun()
    
    st.divider()
    
    # Image display area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if current_item['type'] == 'text_to_image':
            st.markdown("**🎨 Generated from prompt:**")
            with st.container():
                st.markdown(f"*\"{current_item['prompt']}\"*")
        else:
            st.markdown("**📸 Original Image:**")
            if current_item.get('original_image'):
                st.image(current_item['original_image'], caption="Original", use_column_width=True)
            if current_item.get('modification_prompt'):
                st.markdown(f"**Transformation:** *{current_item['modification_prompt']}*")
    
    with col2:
        st.markdown("**✨ Generated Result:**")
        st.image(current_item['image'], caption="Generated", use_column_width=True)
    
    st.divider()
    
    # Action buttons and controls
    st.markdown("### 🎮 Review Actions")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Accept", type="primary", use_container_width=True, help="Save image to output folder"):
            accept_image(current_item)
    
    with col2:
        if st.button("❌ Reject", use_container_width=True, help="Discard this image"):
            reject_image()
    
    with col3:
        modify_prompt = st.text_input(
            "🔄 Transform with new prompt:", 
            key="modify_prompt",
            placeholder="Enter transformation instructions..."
        )
        
        col3a, col3b = st.columns([1, 1])
        with col3a:
            if st.button("🔄 Redo", use_container_width=True, disabled=not modify_prompt.strip(), help="Regenerate with new prompt"):
                if modify_prompt.strip():
                    modify_image(current_item, modify_prompt)
        
        with col3b:
            if st.button("🗑️ Remove", use_container_width=True, help="Remove from queue without saving"):
                remove_current_image()

def thumbnail_sidebar():
    """Right sidebar showing thumbnail grid of all images"""
    st.markdown("### 🖼️ Image Gallery")
    
    if not st.session_state.review_queue:
        st.info("No images to display")
        return
    
    # Statistics at top
    total_images = len(st.session_state.review_queue)
    generating_count = st.session_state.image_states.count('generating')
    ready_count = st.session_state.image_states.count('ready')
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total_images)
    with col2:
        st.metric("Ready", ready_count)
    
    st.divider()
    
    # Thumbnail grid
    st.markdown("**Click image to select:**")
    
    # Create thumbnail grid (3 columns for better fit)
    cols = st.columns(3)
    
    for i, item in enumerate(st.session_state.review_queue):
        col_idx = i % 3
        
        with cols[col_idx]:
            # Determine status and styling
            is_selected = i == st.session_state.selected_image_index
            status = st.session_state.image_states[i] if i < len(st.session_state.image_states) else 'ready'
            
            # Create clickable thumbnail
            if st.button(
                f"#{i+1}",
                key=f"thumb_{i}",
                help=f"Click to select image {i+1}",
                use_container_width=True
            ):
                st.session_state.selected_image_index = i
                st.rerun()
            
            # Show thumbnail image
            if is_selected:
                st.markdown("🟢 **Selected**")
            
            if item['image'] is not None:
                st.image(item['image'], use_column_width=True)
            else:
                # Show placeholder for generating images
                st.markdown("🔄 **Generating...**")
                st.empty()  # Placeholder space
            
            # Show status and prompt preview
            if status == 'generating':
                st.markdown("🟡 Generating...")
            elif status == 'ready':
                st.markdown("🟢 Ready")
            
            # Show truncated prompt
            if item['type'] == 'text_to_image':
                prompt_preview = item['prompt'][:30] + "..." if len(item['prompt']) > 30 else item['prompt']
                st.caption(f"Prompt: {prompt_preview}")
            else:
                st.caption(f"Modified: {item.get('original_filename', 'Image')}")

def generate_from_prompts(prompts: List[str]):
    """Generate images from text prompts in parallel"""
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
    
    # DON'T rerun immediately - let the function continue
    
    # Add tasks to processing queue
    add_log(f"🔄 Starting parallel execution with {len(prompts)} tasks...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        add_log("📋 Creating futures...")
        futures = []
        for i, prompt in enumerate(prompts):
            queue_index = len(st.session_state.review_queue) - len(prompts) + i
            add_log(f"🎯 Submitting task {i+1}: {prompt[:30]}...")
            future = executor.submit(ai_generator.generate_from_text, prompt)
            futures.append((future, prompt, queue_index))
        
        add_log(f"✅ All {len(futures)} tasks submitted to executor")
        
        # Process completed tasks
        progress_bar = st.progress(0)
        status_text = st.empty()
        completed = 0
        
        add_log("⏳ Waiting for task completion...")
        for future in concurrent.futures.as_completed([f for f, _, _ in futures]):
            prompt, queue_index = next((p, qi) for f, p, qi in futures if f == future)
            add_log(f"📥 Task completed for: {prompt[:30]}...")
            try:
                status_text.info(f"🎨 Processing: {prompt[:40]}...")
                image = future.result()
                if image and queue_index < len(st.session_state.review_queue):
                    # Update the existing item with the generated image
                    st.session_state.review_queue[queue_index]['image'] = image
                    st.session_state.review_queue[queue_index]['status'] = 'ready'
                    if queue_index < len(st.session_state.image_states):
                        st.session_state.image_states[queue_index] = 'ready'
                    st.session_state.stats['generated'] += 1
                completed += 1
                progress_bar.progress(completed / len(prompts))
                status_text.success(f"✅ Completed {completed}/{len(prompts)} images")
            except Exception as e:
                st.error(f"Error generating image for prompt: {prompt[:50]}... - {str(e)}")
                # Mark as failed
                if queue_index < len(st.session_state.image_states):
                    st.session_state.image_states[queue_index] = 'failed'
                completed += 1
                progress_bar.progress(completed / len(prompts))
    
    st.success(f"Generated {len(prompts)} images! Check the thumbnail gallery on the right.")
    st.rerun()

def process_images(uploaded_files, modification_prompt: str):
    """Process uploaded images with AI transformation"""
    ai_generator = AIImageGenerator()
    
    # Add placeholder items with 'generating' status
    for uploaded_file in uploaded_files:
        original_image = Image.open(uploaded_file)
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
    
    st.info(f"Started processing {len(uploaded_files)} images...")
    st.rerun()
    
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        queue_index = len(st.session_state.review_queue) - len(uploaded_files) + i
        try:
            original_image = Image.open(uploaded_file)
            modified_image = ai_generator.modify_image(original_image, modification_prompt)
            
            if modified_image and queue_index < len(st.session_state.review_queue):
                # Update the existing item with the generated image
                st.session_state.review_queue[queue_index]['image'] = modified_image
                st.session_state.review_queue[queue_index]['status'] = 'ready'
                if queue_index < len(st.session_state.image_states):
                    st.session_state.image_states[queue_index] = 'ready'
                st.session_state.stats['generated'] += 1
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            # Mark as failed
            if queue_index < len(st.session_state.image_states):
                st.session_state.image_states[queue_index] = 'failed'
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    st.success(f"Transformed {len(uploaded_files)} images! Check the thumbnail gallery on the right.")
    st.rerun()

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
        st.session_state.review_queue.pop(current_index)
        if current_index < len(st.session_state.image_states):
            st.session_state.image_states.pop(current_index)
        
        # Adjust selected index if necessary
        if st.session_state.selected_image_index >= len(st.session_state.review_queue):
            st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
        
        st.success(f"Image saved to {filepath}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error saving image: {str(e)}")

def reject_image():
    """Reject the current image"""
    current_index = st.session_state.selected_image_index
    st.session_state.stats['rejected'] += 1
    st.session_state.review_queue.pop(current_index)
    if current_index < len(st.session_state.image_states):
        st.session_state.image_states.pop(current_index)
    
    # Adjust selected index if necessary
    if st.session_state.selected_image_index >= len(st.session_state.review_queue):
        st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
    
    st.success("Image rejected and removed from queue")
    st.rerun()

def remove_current_image():
    """Remove current image from queue without changing stats"""
    current_index = st.session_state.selected_image_index
    st.session_state.review_queue.pop(current_index)
    if current_index < len(st.session_state.image_states):
        st.session_state.image_states.pop(current_index)
    
    # Adjust selected index if necessary
    if st.session_state.selected_image_index >= len(st.session_state.review_queue):
        st.session_state.selected_image_index = max(0, len(st.session_state.review_queue) - 1)
    
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

def modify_image(current_item, modify_prompt: str):
    """Request transformation of the current image"""
    ai_generator = AIImageGenerator()
    
    try:
        if current_item['type'] == 'text_to_image':
            # Combine original prompt with transformation
            new_prompt = f"{current_item['prompt']} {modify_prompt}"
            new_image = ai_generator.generate_from_text(new_prompt)
        else:
            # Transform the original image with new prompt
            new_image = ai_generator.modify_image(current_item['original_image'], modify_prompt)
        
        if new_image:
            # Add to queue and mark current for removal
            st.session_state.review_queue.append({
                **current_item,
                'image': new_image,
                'timestamp': time.time()
            })
            st.session_state.image_states.append('ready')
            
            # Remove current image
            current_index = st.session_state.selected_image_index
            st.session_state.review_queue.pop(current_index)
            if current_index < len(st.session_state.image_states):
                st.session_state.image_states.pop(current_index)
            
            st.session_state.stats['generated'] += 1
            
            # Select the newly added image (now at the end)
            st.session_state.selected_image_index = len(st.session_state.review_queue) - 1
            
            st.success("Image transformed! New version selected.")
            st.rerun()
    
    except Exception as e:
        st.error(f"Error transforming image: {str(e)}")

if __name__ == "__main__":
    main()