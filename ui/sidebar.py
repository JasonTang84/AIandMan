"""
Sidebar UI components for input workflows.
"""
import streamlit as st
from utils import parse_text_prompts
from background_tasks import generate_from_prompts, process_images
from PIL import Image


def render_sidebar():
   
    # Image quality configuration
    render_image_quality_setting()
    
    # Statistics section
    render_statistics()
    
    # Text-to-Image workflow
    st.header("📝 Text-to-Image")
    text_to_image_interface()
    
    # Image to Image workflow
    st.header("🖼️ Image to Image")
    image_modification_interface()


def render_image_quality_setting():
    """Render the image quality and resolution settings"""
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Quality setting for both generation and modification
        if 'image_quality' not in st.session_state:
            st.session_state.image_quality = "medium"
        st.session_state.image_quality = st.selectbox(
            "Quality",
            options=["low", "medium", "high"],
            index=["low", "medium", "high"].index(st.session_state.image_quality),
            help="Quality setting for both generation and modification"
        )
    
    with col2:
        # Resolution setting for both generation and modification
        if 'image_resolution' not in st.session_state:
            st.session_state.image_resolution = "1024x1536"
        st.session_state.image_resolution = st.selectbox(
            "Image Resolution",
            options=["1024x1024", "1024x1536", "1536x1024"],
            index=["1024x1024", "1024x1536", "1536x1024"].index(st.session_state.image_resolution),
            help="Resolution setting for both generation and modification"
        )


def render_statistics():
    """Render the statistics section"""
    st.header("Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Generated", st.session_state.stats['generated'])
    with col2:
        st.metric("Accepted", st.session_state.stats['accepted'])
    with col3:
        st.metric("Rejected", st.session_state.stats['rejected'])


def text_to_image_interface():
    """Text-to-image upload and generation interface"""
    st.write("Upload a text file with prompts separated by semicolons (`;`)")
    
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['txt'],
        key="text_file",
        help="Maximum 150 prompts • TXT"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        prompts = parse_text_prompts(content)
        
        if len(prompts) > 150:
            st.error(f"Too many prompts! Found {len(prompts)} prompts, but maximum allowed is 150. Please reduce the number of prompts in your file.")
        elif len(prompts) == 0:
            st.warning("No prompts found in the file. Make sure prompts are separated by semicolons (;)")
        else:
            st.success(f"Found {len(prompts)} prompts")
            
            if st.button("Generate Images", type="primary", use_container_width=True):
                generate_from_prompts(prompts)


def image_modification_interface():
    """Image-to-image upload and transformation interface"""   
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
