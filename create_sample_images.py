"""
Quick test script to create sample images for mock testing.
Run this to generate some test images if you don't have any.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_images():
    """Create sample test images for the mock function"""
    mock_folder = "mock_images"
    if not os.path.exists(mock_folder):
        os.makedirs(mock_folder)
    
    # Create sample images with different sizes and colors
    samples = [
        {"name": "test1.jpg", "size": (400, 300), "color": (255, 100, 100), "text": "Sample 1"},
        {"name": "test2.png", "size": (300, 400), "color": (100, 255, 100), "text": "Sample 2"}, 
        {"name": "test3.jpg", "size": (350, 350), "color": (100, 100, 255), "text": "Sample 3"},
        {"name": "test4.png", "size": (500, 200), "color": (255, 255, 100), "text": "Wide Image"},
        {"name": "test5.jpg", "size": (200, 500), "color": (255, 100, 255), "text": "Tall Image"},
    ]
    
    for sample in samples:
        # Create image
        img = Image.new('RGB', sample["size"], sample["color"])
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
            
        text = sample["text"]
        if font:
            # Get text size and center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (sample["size"][0] - text_width) // 2
            y = (sample["size"][1] - text_height) // 2
            draw.text((x, y), text, fill=(0, 0, 0), font=font)
        else:
            # Fallback without font
            draw.text((50, 50), text, fill=(0, 0, 0))
        
        # Save image
        img_path = os.path.join(mock_folder, sample["name"])
        img.save(img_path)
        print(f"Created: {img_path}")
    
    print(f"\nCreated {len(samples)} sample images in {mock_folder}/")
    print("You can now run the Streamlit app to see the mock thumbnails!")

if __name__ == "__main__":
    create_sample_images()
