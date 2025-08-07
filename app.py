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

def main():
    st.set_page_config(page_title="AIandMan", page_icon="🎨", layout="wide")
    
    st.title("🎨 AIandMan")
    st.subheader("AI & Human Collaboration Tool")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.session_state.output_folder = st.text_input(
            "Output Folder", 
            value=st.session_state.output_folder,
            help="Folder where accepted images will be saved"
        )
        
        st.header("Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Generated", st.session_state.stats['generated'])
        with col2:
            st.metric("Accepted", st.session_state.stats['accepted'])
        with col3:
            st.metric("Rejected", st.session_state.stats['rejected'])
    
    # Main interface
    tab1, tab2, tab3 = st.tabs(["📝 Text-to-Image", "🖼️ Image Modification", "👁️ Review Queue"])
    
    with tab1:
        text_to_image_interface()
    
    with tab2:
        image_modification_interface()
    
    with tab3:
        review_interface()
    
    # Background task status
    if st.session_state.processing_tasks:
        st.info(f"🔄 Processing {len(st.session_state.processing_tasks)} tasks in background...")

def text_to_image_interface():
    st.header("Text-to-Image Generation")
    st.write("Upload a text file with prompts separated by semicolons (`;`)")
    
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['txt'],
        key="text_file"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        prompts = parse_text_prompts(content)
        
        st.write(f"Found {len(prompts)} prompts:")
        with st.expander("Preview prompts"):
            for i, prompt in enumerate(prompts[:5]):  # Show first 5
                st.write(f"{i+1}. {prompt[:100]}...")
            if len(prompts) > 5:
                st.write(f"... and {len(prompts) - 5} more")
        
        if st.button("Generate Images", type="primary"):
            generate_from_prompts(prompts)

def image_modification_interface():
    st.header("Image Modification")
    st.write("Upload images for AI-powered enhancement or modification")
    
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key="image_files"
    )
    
    modification_prompt = st.text_area(
        "Modification Instructions (optional)",
        placeholder="e.g., 'Make it more colorful and vibrant' or leave empty for default enhancement",
        height=100
    )
    
    if uploaded_files and st.button("Process Images", type="primary"):
        process_images(uploaded_files, modification_prompt)

def review_interface():
    st.header("Image Review Queue")
    
    if not st.session_state.review_queue:
        st.info("No images in review queue. Generate some images first!")
        return
    
    if st.session_state.review_queue:
        current_item = st.session_state.review_queue[0]
        st.write(f"Reviewing {len(st.session_state.review_queue)} images (showing first)")
        
        # Display image and prompt
        col1, col2 = st.columns(2)
        
        with col1:
            if current_item['type'] == 'text_to_image':
                st.write("**Generated from prompt:**")
                st.write(f"*{current_item['prompt']}*")
            else:
                st.write("**Original Image:**")
                if current_item.get('original_image'):
                    st.image(current_item['original_image'], caption="Original")
        
        with col2:
            st.write("**Generated Image:**")
            st.image(current_item['image'], caption="Generated")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Accept", type="primary"):
                accept_image(current_item)
        
        with col2:
            if st.button("❌ Reject"):
                reject_image()
        
        with col3:
            modify_prompt = st.text_input("Modify prompt:", key="modify_prompt")
        
        with col4:
            if st.button("🔄 Modify") and modify_prompt:
                modify_image(current_item, modify_prompt)

def generate_from_prompts(prompts: List[str]):
    """Generate images from text prompts in parallel"""
    ai_generator = AIImageGenerator()
    
    # Add tasks to processing queue
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for prompt in prompts:
            future = executor.submit(ai_generator.generate_from_text, prompt)
            futures.append((future, prompt))
        
        # Process completed tasks
        progress_bar = st.progress(0)
        completed = 0
        
        for future, prompt in concurrent.futures.as_completed([f for f, _ in futures]):
            try:
                image = future.result()
                if image:
                    st.session_state.review_queue.append({
                        'type': 'text_to_image',
                        'image': image,
                        'prompt': prompt,
                        'timestamp': time.time()
                    })
                    st.session_state.stats['generated'] += 1
                completed += 1
                progress_bar.progress(completed / len(prompts))
            except Exception as e:
                st.error(f"Error generating image for prompt: {prompt[:50]}... - {str(e)}")
    
    st.success(f"Generated {len(prompts)} images! Check the Review Queue.")
    st.rerun()

def process_images(uploaded_files, modification_prompt: str):
    """Process uploaded images with AI modification"""
    ai_generator = AIImageGenerator()
    
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            original_image = Image.open(uploaded_file)
            modified_image = ai_generator.modify_image(original_image, modification_prompt)
            
            if modified_image:
                st.session_state.review_queue.append({
                    'type': 'image_modification',
                    'image': modified_image,
                    'original_image': original_image,
                    'modification_prompt': modification_prompt,
                    'original_filename': uploaded_file.name,
                    'timestamp': time.time()
                })
                st.session_state.stats['generated'] += 1
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    st.success(f"Processed {len(uploaded_files)} images! Check the Review Queue.")
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
            filename = f"modified_{base_name}_{timestamp}.png"
        
        # Save image
        filepath = os.path.join(st.session_state.output_folder, filename)
        current_item['image'].save(filepath)
        
        # Update stats and queue
        st.session_state.stats['accepted'] += 1
        st.session_state.review_queue.pop(0)
        
        st.success(f"Image saved to {filepath}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error saving image: {str(e)}")

def reject_image():
    """Reject the current image"""
    st.session_state.stats['rejected'] += 1
    st.session_state.review_queue.pop(0)
    st.info("Image rejected")
    st.rerun()

def modify_image(current_item, modify_prompt: str):
    """Request modification of the current image"""
    ai_generator = AIImageGenerator()
    
    try:
        if current_item['type'] == 'text_to_image':
            # Combine original prompt with modification
            new_prompt = f"{current_item['prompt']} {modify_prompt}"
            new_image = ai_generator.generate_from_text(new_prompt)
        else:
            # Modify the original image with new prompt
            new_image = ai_generator.modify_image(current_item['original_image'], modify_prompt)
        
        if new_image:
            # Add to queue and remove current
            st.session_state.review_queue.append({
                **current_item,
                'image': new_image,
                'timestamp': time.time()
            })
            st.session_state.review_queue.pop(0)
            st.session_state.stats['generated'] += 1
            
            st.success("Image modified! Added to queue.")
            st.rerun()
    
    except Exception as e:
        st.error(f"Error modifying image: {str(e)}")

if __name__ == "__main__":
    main()