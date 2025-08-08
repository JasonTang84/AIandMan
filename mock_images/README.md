# Mock Images Folder

This folder is used for testing the thumbnail sidebar functionality.

## How to use:

1. Place your test images in this folder (jpg, png, gif, bmp, tiff formats supported)
2. Run the application - the mock function will automatically load these images
3. The thumbnail sidebar will display your test images for styling and layout debugging

## To disable mock data:

Comment out this line in `ui/thumbnail_sidebar.py`:
```python
# load_mock_images()  # Comment this line to disable mock data
```

## Example images you can add:
- test1.jpg
- test2.png  
- sample_image.gif
- Any image files you want to test with

The mock function will also add some "generating" placeholders to test the full UI.
