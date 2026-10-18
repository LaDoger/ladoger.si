# This script converts all .png files in the same folder to .jpg format.
# Each converted file keeps the same name but with a .jpg extension.
# The quality of the output JPG files is set to 80 (adjustable, 0-100).
# Requires the Pillow library: install with 'pip install Pillow'

from PIL import Image
import os

# Get the directory of the script (where the .png files are located)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Loop through all files in the directory
for filename in os.listdir(current_dir):
    # Check if the file is a .png file
    if filename.lower().endswith('.png'):
        try:
            # Construct full file paths
            png_path = os.path.join(current_dir, filename)
            # Create the new .jpg filename
            jpg_filename = os.path.splitext(filename)[0] + '.jpg'
            jpg_path = os.path.join(current_dir, jpg_filename)
            
            # Open the PNG image
            with Image.open(png_path) as img:
                # Convert to RGB if necessary (JPEG doesn't support transparency)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Save as JPG with quality=80
                img.save(jpg_path, 'JPEG', quality=80)
                print(f"Successfully converted '{filename}' to '{jpg_filename}' with quality=80")
                
        except Exception as e:
            print(f"Failed to convert '{filename}' due to error: {str(e)}")

print("Conversion process completed. All .png files in the folder have been processed.")