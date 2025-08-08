# Azure OpenAI Setup Guide

This guide explains how to set up your environment to use Azure OpenAI with GPT-image-1 for image generation.

## Prerequisites

1. **Azure Subscription**: You need an active Azure subscription
2. **Azure OpenAI Resource**: Create an Azure OpenAI resource in a supported region
3. **GPT-image-1 Access**: Apply for limited access to GPT-image-1 model

## Step 1: Create Azure OpenAI Resource

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new "Azure OpenAI" resource
3. Choose a supported region for GPT-image-1:
   - West US 3 (Global Standard)
   - UAE North (Global Standard)
   - Poland Central (Global Standard)

## Step 2: Request GPT-image-1 Access

GPT-image-1 is in limited access preview. You need to apply for access:

1. Go to the [GPT-image-1 Access Request Form](https://aka.ms/oai/gptimage1access)
2. Fill out the application form
3. Wait for approval (this may take some time)

## Step 3: Deploy the Model

Once you have access:

1. In your Azure OpenAI resource, go to "Model deployments"
2. Click "Create new deployment"
3. Select "gpt-image-1" as the model
4. Give it a deployment name (e.g., "gpt-image-1-deployment")
5. Deploy the model

## Step 4: Get Your Credentials

1. In your Azure OpenAI resource, go to "Keys and Endpoint"
2. Copy one of the API keys
3. Copy the endpoint URL

## Step 5: Set Environment Variables

Create a `.env` file in your project root or set these environment variables:

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
```

**Important**: Replace `your_api_key_here` and `your-resource-name` with your actual values.

## Step 6: Update Your Code

The code has been updated to use Azure OpenAI with GPT-image-1. Key changes:

- Uses `AzureOpenAI` client instead of `OpenAI`
- Model changed from "dall-e-3" to "gpt-image-1"
- API version set to "2025-04-01-preview"
- Handles base64 image responses (GPT-image-1 default)

## Step 7: Install Required Packages

Make sure you have the latest Azure OpenAI SDK:

```bash
pip install openai>=1.12.0 pillow requests python-dotenv
```

## Usage Example

```python
from ai_integration import AIImageGenerator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create generator instance
generator = AIImageGenerator()

# Generate an image
image = generator.generate_from_text("A beautiful sunset over mountains")
if image:
    image.save("generated_image.png")
```

## Troubleshooting

### Common Issues:

1. **Access Denied**: Make sure you've been approved for GPT-image-1 access
2. **Model Not Found**: Ensure you've deployed the gpt-image-1 model in your Azure OpenAI resource
3. **Authentication Error**: Check your API key and endpoint URL
4. **Region Not Supported**: Make sure your Azure OpenAI resource is in a supported region

### Error Messages:

- `ContentFilter`: Your prompt was filtered by Azure's content policy
- `Model not found`: The model hasn't been deployed in your resource
- `Unauthorized`: Check your API key and endpoint

## GPT-image-1 Features

GPT-image-1 offers several improvements over DALL-E 3:

- **Better Quality**: Three quality levels (low, medium, high)
- **Multiple Sizes**: 1024x1024, 1024x1536, 1536x1024
- **Image Editing**: Direct image editing capabilities
- **Streaming**: Partial image generation for faster feedback
- **Better Input Fidelity**: Preserves faces and features better during edits

## API Differences

### Quality Options:
- GPT-image-1: "low", "medium", "high" (default: "high")
- DALL-E 3: "standard", "hd"

### Response Format:
- GPT-image-1: Always returns base64 encoded images
- DALL-E 3: Can return URLs or base64

### Image Editing:
- GPT-image-1: Native image editing support
- DALL-E 3: Limited editing capabilities
