import os
from openai import AzureOpenAI
from PIL import Image
import io
import requests
from typing import Optional
import base64
from dotenv import load_dotenv

class AIImageGenerator:
    def __init__(self):
        print("🔧 AIImageGenerator: Starting initialization...")
        
        # Reload environment variables to get latest values
        load_dotenv(override=True)
        
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2025-04-01-preview",
            azure_endpoint=endpoint
        )
        self.default_size = "1024x1536"
        self.default_quality = "low"  # GPT-image-1 supports low, medium, high
        
        print("✅ AIImageGenerator: Initialization complete")
    
    def generate_from_text(self, prompt: str, size: str = None, quality: str = None, logger_callback=None) -> Optional[Image.Image]:
        """Generate an image from a text prompt using GPT-image-1"""
        try:
            print(f"🔄 Generating image: {prompt[:50]}...")
            if logger_callback:
                logger_callback(f"🔄 Starting generation: {prompt[:50]}...")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size or self.default_size,
                quality=quality or self.default_quality,
                n=1,
            )
            
            print("✅ Image generated successfully")
            if logger_callback:
                logger_callback(f"✅ Generation completed: {prompt[:50]}...")
            
            # GPT-image-1 returns base64 encoded images by default
            image_b64 = response.data[0].b64_json
            return self._decode_base64_image(image_b64)
            
        except Exception as e:
            error_msg = f"❌ Generation failed: {prompt[:50]}... - {str(e)}"
            print(error_msg)
            if logger_callback:
                logger_callback(error_msg)
            # Re-raise the exception so the background task can handle cancellation
            raise e
    
    def modify_image(self, image: Image.Image, prompt: str = None, quality: str = None, logger_callback=None) -> Optional[Image.Image]:
        """Modify an existing image using GPT-image-1 edit API via direct HTTP request"""
        try:
            print("🔄 Modifying image...")
            if logger_callback:
                logger_callback(f"🔄 Starting modification: {prompt[:50] if prompt else 'Enhancement'}...")
            
            # Use default enhancement prompt if none provided
            if not prompt:
                prompt = "Enhance this image to make it more vibrant, clear, and visually appealing while maintaining its original composition and style."
            
            # Convert PIL Image to bytes for multipart upload
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Construct the edit endpoint URL manually (following Microsoft Learn guidance)
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            deployment_name = "gpt-image-1"  # Your deployment name
            api_version = "2025-04-01-preview"
            
            edit_url = f"{azure_endpoint}/openai/deployments/{deployment_name}/images/edits?api-version={api_version}"           
            # Prepare headers
            headers = {
                'api-key': os.getenv('AZURE_OPENAI_API_KEY')
            }
            
            # Prepare multipart form data exactly as shown in Microsoft Learn example
            # Note: Using just "image" as field name, not "image[]"
            files = {
                'image': ('image.png', img_byte_arr.getvalue(), 'image/png')
            }
            
            data = {
                'model': deployment_name,
                'prompt': prompt,
                'size': self.default_size,
                'quality': quality or self.default_quality,
                'n': '1'
            }
            
            # Make the HTTP request using requests library
            response = requests.post(edit_url, headers=headers, files=files, data=data)
            
            # Print detailed error info if request fails
            if response.status_code != 200:
                error_details = f"HTTP {response.status_code}: {response.text}"
                print(f"❌ HTTP Status: {response.status_code}")
                print(f"❌ Response Headers: {dict(response.headers)}")
                print(f"❌ Response Text: {response.text}")
                if logger_callback:
                    logger_callback(f"❌ HTTP Error: {error_details}")
            
            response.raise_for_status()
            
            print("✅ Image modified successfully")
            if logger_callback:
                logger_callback(f"✅ Modification completed: {prompt[:50]}...")
            
            # Parse response JSON
            response_data = response.json()
            
            # GPT-image-1 returns base64 encoded images by default
            image_b64 = response_data['data'][0]['b64_json']
            return self._decode_base64_image(image_b64)
            
        except Exception as e:
            error_msg = f"❌ Modification failed: {prompt[:50] if prompt else 'Enhancement'}... - {str(e)}"
            print(error_msg)
            if logger_callback:
                logger_callback(error_msg)
            # Re-raise the exception so the background task can handle cancellation
            raise e
    
      
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