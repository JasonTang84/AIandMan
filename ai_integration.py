import os
from openai import AzureOpenAI
from PIL import Image
import io
import requests
from typing import Optional
import base64

class AIImageGenerator:
    def __init__(self):
        print("🔧 AIImageGenerator: Starting initialization...")
        
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2025-04-01-preview",
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        self.default_size = "1024x1024"
        self.default_quality = "low"  # GPT-image-1 supports low, medium, high
        
        print("✅ AIImageGenerator: Initialization complete")
    
    def generate_from_text(self, prompt: str, size: str = None, quality: str = None) -> Optional[Image.Image]:
        """Generate an image from a text prompt using GPT-image-1"""
        try:
            print(f"🔄 Generating image: {prompt[:50]}...")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size or self.default_size,
                quality=quality or self.default_quality,
                n=1,
            )
            
            print("✅ Image generated successfully")
            
            # GPT-image-1 returns base64 encoded images by default
            image_b64 = response.data[0].b64_json
            return self._decode_base64_image(image_b64)
            
        except Exception as e:
            print(f"❌ Error generating image: {str(e)}")
            return None
    
    def modify_image(self, image: Image.Image, prompt: str = None) -> Optional[Image.Image]:
        """Modify an existing image using GPT-image-1 edit functionality"""
        try:
            print("🔄 Modifying image...")
            
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Use default enhancement prompt if none provided
            if not prompt:
                prompt = "Enhance this image to make it more vibrant, clear, and visually appealing while maintaining its original composition and style."
            
            # GPT-image-1 supports image editing
            response = self.client.images.edit(
                image=img_byte_arr,
                prompt=prompt,
                model="gpt-image-1",
                size=self.default_size,
                quality=self.default_quality,
                n=1,
            )
            
            print("✅ Image modified successfully")
            
            # GPT-image-1 returns base64 encoded images
            image_b64 = response.data[0].b64_json
            return self._decode_base64_image(image_b64)
            
        except Exception as e:
            print(f"❌ Error modifying image: {str(e)}")
            # Fallback: return original image if modification fails
            return image
    
    def create_variation(self, image: Image.Image) -> Optional[Image.Image]:
        """Create a variation of an existing image using GPT-image-1"""
        try:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            # Ensure image is in RGBA format and under size limit
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Resize if too large (Azure OpenAI requires < 50MB)
            if image.width > 1024 or image.height > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Use GPT-image-1's variation capabilities
            response = self.client.images.edit(
                image=img_byte_arr,
                prompt="Create a variation of this image with similar style and composition",
                model="gpt-image-1",
                size=self.default_size,
                quality=self.default_quality,
                n=1
            )
            
            # GPT-image-1 returns base64 encoded images
            image_b64 = response.data[0].b64_json
            return self._decode_base64_image(image_b64)
            
        except Exception as e:
            print(f"Error creating image variation: {str(e)}")
            return None
    
    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download an image from a URL and return as PIL Image"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return None
    
    def _decode_base64_image(self, base64_string: str) -> Optional[Image.Image]:
        """Decode a base64 string to PIL Image"""
        try:
            image_data = base64.b64decode(base64_string)
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            print(f"Error decoding base64 image: {str(e)}")
            return None
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')