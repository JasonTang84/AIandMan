# AIandMan
**AI & Human Collaboration Tool**

A streamlined Streamlit-based application that enables seamless collaboration between AI image generation and human curation, powered by GPT-image-1.

## Overview

AIandMan is an interactive tool that allows users to generate and modify images using AI while maintaining human oversight and quality control. The application supports both batch text-to-image generation and image-to-image modification workflows.

## Key Features

### Input Methods
- **Text File Processing**: Each time upload one text file containing multiple prompts separated by semicolons (`;`) for batch image generation
- **Image Upload**: Each time upload single or multiple images for AI-powered modification and enhancement

### Core Functionality

#### 1. Batch Text-to-Image Generation
- Parse text file with semicolon-separated prompts
- Generate unique images for each prompt using GPT-IMAGE-1
- Process multiple prompts in parallel for efficient workflow

#### 2. Image-to-Image Transformation
- Upload existing images for AI-powered transformation and enhancement
- Apply custom transformation prompts to uploaded images
- Maintain original image context while applying creative transformations

#### 3. Parallel Processing
- All image generation and transformation tasks run concurrently
- Efficient resource utilization for faster results
- Background processing for seamless user experience

#### 4. Interactive Review System
If input is an image, showing before/after image; If input is a prompt, showing image with prompt. Then let user to decide
- **Accept**: Save approved images to configured output folder
- **Reject**: Discard unwanted images without saving
- **Modify**: Provide additional prompts for image transformation (queued in background)

#### 5. Queue Management
- Organized queue system for reviewing multiple generated images
- Sequential review process to prevent overwhelming the user
- Clear workflow for handling multiple simultaneous generations

#### 6. User Interface
- **Status Dashboard**: Real-time display of generation progress
- **Statistics Panel**: Track counts of generated, accepted, and rejected images
- **Background Task Monitor**: Visual indication of ongoing processes
- **Simple, Intuitive Controls**: Streamlined interface for efficient workflow

## Workflow

1. **Input**: Upload text file with prompts or image files
2. **Processing**: AI generates/transforms images in parallel
3. **Review**: Sequential presentation of generated images
4. **Decision**: Accept, reject, or request transformations for each image
5. **Output**: Approved images saved to user-configured directory

## Technical Stack
- **Frontend**: Streamlit
- **AI Engine**: GPT-Image-1
- **Processing**: Parallel task execution
- **Storage**: Local file system with user-configurable output paths

## Setup & Authentication

### Password Protection
AIandMan includes a simple password authentication system to protect access:

- **Default Password**: `aiandman2025`
- **Custom Password**: Set `APP_PASSWORD` in your `.env` file
- **Development Mode**: Set `STREAMLIT_ENV=development` to show password hints

### Configuration
1. Copy `.env.example` to `.env`
2. Configure your Azure OpenAI credentials
3. (Optional) Set a custom password with `APP_PASSWORD`

### First Launch
When you start the application, you'll be prompted to enter the password before accessing the main interface. The logout button is available in the sidebar once authenticated.