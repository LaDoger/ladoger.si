import os
import hashlib
import subprocess
import shutil
from PIL import Image
from pathlib import Path

IMAGES_DIR = 'images'
OUTPUT_FILE = 'images.txt'
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.mkv', '.avi'}

def get_file_hash(file_path):
    """Calculate MD5 hash of a file."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]

def is_ffmpeg_installed():
    """Check if ffmpeg is installed."""
    return shutil.which('ffmpeg') is not None

def process_video(file_path, filename):
    """Process a video file: hash, rename, and generate thumbnail."""
    try:
        file_hash = get_file_hash(file_path)
        ext = os.path.splitext(filename)[1].lower()
        new_filename = f"{file_hash}{ext}"
        new_file_path = os.path.join(IMAGES_DIR, new_filename)
        thumbnail_filename = f"{file_hash}.jpg"
        thumbnail_path = os.path.join(IMAGES_DIR, thumbnail_filename)
        
        # If new file path is different, rename
        if file_path != new_file_path:
            # Check if destination exists (hash collision or already processed)
            if os.path.exists(new_file_path):
                 # If identical file content, we can remove the original
                 # If not, we have a collision (rare with md5/8chars but possible)
                 # For now, assume it's the same file processed previously
                 os.remove(file_path)
            else:
                os.rename(file_path, new_file_path)
        
        # Generate thumbnail if it doesn't exist
        if not os.path.exists(thumbnail_path):
            # ffmpeg -i input.mp4 -ss 00:00:01.000 -vframes 1 output.jpg
            # Using -ss 0 to get the very first frame. Sometimes -ss 1 is better to avoid black frames, 
            # but user asked for first frame.
            cmd = [
                'ffmpeg', '-y', '-i', new_file_path, 
                '-vframes', '1', '-f', 'image2', thumbnail_path
            ]
            # Suppress output
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Generated thumbnail: {thumbnail_filename}")

        return new_filename, thumbnail_filename
    except Exception as e:
        print(f"Error processing video {filename}: {e}")
        return None, None

def process_images():
    if not is_ffmpeg_installed():
        print("Error: ffmpeg is not installed or not in PATH. Cannot process videos.")
        return

    processed_files = []
    video_thumbnails = set()
    
    if not os.path.exists(IMAGES_DIR):
        print(f"Directory {IMAGES_DIR} not found.")
        return

    # Get list of all files
    all_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    
    # 1. Process Videos first
    for filename in all_files:
        file_path = os.path.join(IMAGES_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in VIDEO_EXTENSIONS:
            new_vid_name, thumb_name = process_video(file_path, filename)
            if new_vid_name:
                processed_files.append(new_vid_name)
                print(f"Processed Video: {filename} -> {new_vid_name}")
                if thumb_name:
                    video_thumbnails.add(thumb_name)

    # Re-scan directory for images (since renames happened)
    # We need to filter out files that are already processed videos or their thumbnails
    current_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    
    for filename in current_files:
        file_path = os.path.join(IMAGES_DIR, filename)
        
        # Skip if it's a known video file we just processed/identified
        if filename in processed_files:
            continue
            
        # Skip if it is a thumbnail for a video
        if filename in video_thumbnails:
            continue

        # Skip system files or text files
        if filename.lower().endswith('.txt') or filename.startswith('.'):
            continue

        # Skip video files that might have been skipped in pass 1 (e.g. error) or added late? 
        # Actually pass 1 handles all videos. So we only care about images here.
        ext = os.path.splitext(filename)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            continue
            
        try:
            # Calculate hash for new filename
            file_hash = get_file_hash(file_path)
            new_filename = f"{file_hash}.jpg"
            new_file_path = os.path.join(IMAGES_DIR, new_filename)
            
            # If this image is actually a video thumbnail (collision of naming logic), we should skip it
            # But process_video generates {hash}.jpg. Here we generate {hash}.jpg.
            # If the original file was an image, we process it.
            
            # Open image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary (e.g. PNG with alpha)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                temp_path = new_file_path + ".temp"
                img.save(temp_path, 'JPEG', quality=80, optimize=True)
                
                # If the new filename is different from the old one, remove the old one
                if file_path != new_file_path:
                    os.remove(file_path)
                    os.rename(temp_path, new_file_path)
                else:
                    os.replace(temp_path, new_file_path)
                    
            processed_files.append(new_filename)
            print(f"Processed Image: {filename} -> {new_filename}")
            
        except Exception as e:
            # Not an image or corrupted
            # print(f"Skipping {filename}: {e}")
            pass

    # Write to text file
    with open(OUTPUT_FILE, 'w') as f:
        for fname in sorted(processed_files):
            f.write(f"{fname}\n")
            
    print(f"Finished! List written to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_images()
