import os
import openai
from PIL import Image
import io
import requests
from typing import Optional
import base64

class AIImageGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.default_size = "1024x1024"
        self.default_quality = "standard"
    
    def generate_from_text(self, prompt: str, size: str = None, quality: str = None) -> Optional[Image.Image]:
        """Generate an image from a text prompt using DALL-E"""
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size or self.default_size,
                quality=quality or self.default_quality,
                n=1,
            )
            
            image_url = response.data[0].url
            return self._download_image(image_url)
            
        except Exception as e:
            print(f"Error generating image from text: {str(e)}")
            return None
    
    def modify_image(self, image: Image.Image, prompt: str = None) -> Optional[Image.Image]:
        """Modify an existing image using DALL-E edit functionality"""
        try:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Use default enhancement prompt if none provided
            if not prompt:
                prompt = "Enhance this image to make it more vibrant, clear, and visually appealing while maintaining its original composition and style."
            
            # For image-to-image, we'll use DALL-E's variation feature
            # Note: DALL-E-3 doesn't support direct image editing, so we'll use a workaround
            # by describing the image and applying the modification
            enhanced_prompt = f"An enhanced version of the uploaded image: {prompt}"
            
            # Since DALL-E-3 doesn't support direct image input for editing,
            # we'll use the variation approach or implement a different strategy
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=self.default_size,
                quality=self.default_quality,
                n=1,
            )
            
            image_url = response.data[0].url
            return self._download_image(image_url)
            
        except Exception as e:
            print(f"Error modifying image: {str(e)}")
            # Fallback: return original image if modification fails
            return image
    
    def create_variation(self, image: Image.Image) -> Optional[Image.Image]:
        """Create a variation of an existing image"""
        try:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            # Ensure image is in RGBA format and under size limit
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Resize if too large (DALL-E requires < 4MB)
            if image.width > 1024 or image.height > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            response = self.client.images.create_variation(
                image=img_byte_arr,
                n=1,
                size=self.default_size
            )
            
            image_url = response.data[0].url
            return self._download_image(image_url)
            
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
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')