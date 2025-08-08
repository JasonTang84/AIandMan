# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIandMan is a Streamlit-based application for AI image generation and human curation using GPT-Image-1. The tool supports batch text-to-image generation and image-to-image transformation with interactive review capabilities.

## Architecture

### Core Components
- **Streamlit Frontend**: Main UI for file uploads, image review, and workflow management
- **AI Integration**: GPT-Image-1 API wrapper for image generation and modification
- **Queue System**: Background task management for parallel image processing
- **File Management**: Input parsing (semicolon-separated text prompts) and output handling
- **Review Interface**: Accept/reject/modify workflow with before/after comparison

### Key Workflows
1. **Text-to-Image**: Parse semicolon-separated prompts from text files → parallel generation → sequential review
2. **Image-to-Image**: Upload images → apply transformations → side-by-side comparison → review
3. **Queue Processing**: Background generation with real-time status updates and statistics

## Development Setup

### Prerequisites
1. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```
   cp .env.example .env
   ```
2. Install dependencies: `pip install -r requirements.txt`

### Running the Application
- Run application: `streamlit run app.py`
- Or use the launcher: `python run.py`
- Development with auto-reload: `streamlit run app.py --reload`
- App will be available at: http://localhost:8502

### New UI Layout
- **Left Sidebar**: Contains all input workflows (Text-to-Image and Image-to-Image) plus configuration and statistics
- **Main Area**: Dedicated to the review queue and user interactions (Accept/Reject/Redo)
- **Queue Management**: Sequential review with preview of upcoming images

## Implementation Notes

- All image processing should run in parallel for efficiency
- UI should show real-time progress and statistics (generated/accepted/rejected counts)
- File uploads support both single text files (with semicolon-separated prompts) and multiple image files
- Output directory should be user-configurable
- Review interface needs clear accept/reject/modify buttons with intuitive workflow
- Background tasks require proper queue management and status tracking

## Key Technical Considerations

- GPT-Image-1 API integration for both text-to-image and image-to-image workflows
- Concurrent processing for multiple image generation tasks
- Streamlit session state management for queue and review workflow
- File handling for various input formats and user-specified output paths