import os
import hashlib
import shutil
import cv2
from PIL import Image

def hash_file(filepath, blocksize=65536):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()[:10]

def is_already_hashed(filename):
    if len(filename) < 10:
        return False
    hex_chars = set('0123456789abcdef')
    return all(c.lower() in hex_chars for c in filename[:10])

def read_existing_txt(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def process_images(directory):
    parent_dir = os.path.dirname(directory)
    square_dir = os.path.join(parent_dir, 'square')
    landscape_dir = os.path.join(parent_dir, 'landscape')
    vertical_dir = os.path.join(parent_dir, 'vertical')

    os.makedirs(square_dir, exist_ok=True)
    os.makedirs(landscape_dir, exist_ok=True)
    os.makedirs(vertical_dir, exist_ok=True)

    square_images = read_existing_txt(os.path.join(square_dir, 'images.txt'))
    landscape_images = read_existing_txt(os.path.join(landscape_dir, 'images.txt'))
    vertical_images = read_existing_txt(os.path.join(vertical_dir, 'images.txt'))

    # Process new files and generate thumbnails
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.png', '.jpg', '.jpeg']:
                if is_already_hashed(filename):
                    file_hash = filename[:10]
                else:
                    file_hash = hash_file(filepath)
                    new_filename = f"{file_hash}"
                    new_original_filename = f"{new_filename}{ext.lower()}"
                    new_original_path = os.path.join(directory, new_original_filename)
                    if filepath != new_original_path:
                        os.rename(filepath, new_original_path)
                        filepath = new_original_path

                with Image.open(filepath) as img:
                    width, height = img.size
                    if width == height:
                        img_dir = square_dir
                        image_list = square_images
                        thumb_size = (512, 512)
                    elif width > height:
                        img_dir = landscape_dir
                        image_list = landscape_images
                        scale = 512 / width
                        thumb_size = (512, int(height * scale))
                    else:
                        img_dir = vertical_dir
                        image_list = vertical_images
                        scale = 512 / height
                        thumb_size = (int(width * scale), 512)

                    thumb_jpg_filename = f"{file_hash}_thumb.jpg"
                    thumb_jpg_path = os.path.join(img_dir, thumb_jpg_filename)
                    
                    if not os.path.exists(thumb_jpg_path):
                        thumb_img = img.resize(thumb_size, Image.LANCZOS)
                        thumb_img.convert('RGB').save(thumb_jpg_path, 'JPEG', quality=80)
                        print(f"Generated new thumbnail: {thumb_jpg_path}")

                    full_jpg_filename = f"{file_hash}.jpg"
                    full_jpg_path = os.path.join(img_dir, full_jpg_filename)
                    if not os.path.exists(full_jpg_path):
                        if ext.lower() == '.png':
                            img.convert('RGB').save(full_jpg_path, 'JPEG', quality=80)
                        else:
                            if filepath != full_jpg_path:
                                shutil.copy2(filepath, full_jpg_path)

                    image_list.add(thumb_jpg_filename)
                    print(f"Added to {img_dir}/images.txt: {thumb_jpg_filename}")

    # Write results
    for dir_path, images in zip([square_dir, landscape_dir, vertical_dir], 
                                [square_images, landscape_images, vertical_images]):
        images_txt_path = os.path.join(dir_path, 'images.txt')
        with open(images_txt_path, 'w') as f:
            for img_name in sorted(images):
                f.write(f"{img_name}\n")
        print(f"Wrote {len(images)} entries to {images_txt_path}")

def process_videos(directory):
    videos_txt_path = os.path.join(directory, 'videos.txt')
    video_list = read_existing_txt(videos_txt_path)

    # Process videos
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext.lower() == '.mp4':
                if is_already_hashed(filename):
                    file_hash = filename[:10]
                else:
                    file_hash = hash_file(filepath)
                    new_filename = f"{file_hash}.mp4"
                    new_path = os.path.join(directory, new_filename)
                    if filepath != new_path:
                        os.rename(filepath, new_path)
                        filepath = new_path

                thumbnail_filename = f"{file_hash}.jpg"
                thumbnail_path = os.path.join(directory, thumbnail_filename)
                
                if not os.path.exists(thumbnail_path):
                    video = cv2.VideoCapture(filepath)
                    success, frame = video.read()
                    if success:
                        cv2.imwrite(thumbnail_path, frame)
                        print(f"Generated new thumbnail: {thumbnail_path}")
                    video.release()

                video_name = f"{file_hash}.mp4"
                video_list.add(video_name)
                print(f"Added to videos.txt: {video_name}")

    with open(videos_txt_path, 'w') as f:
        for video_name in sorted(video_list):
            f.write(f"{video_name}\n")
    print(f"Wrote {len(video_list)} entries to {videos_txt_path}")

def process_frens(directory):
    os.makedirs(directory, exist_ok=True)
    frens_txt_path = os.path.join(directory, 'frens.txt')
    frens_list = read_existing_txt(frens_txt_path)

    # Process new files
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.jpg', '.jpeg']:
                if is_already_hashed(filename):
                    file_hash = filename[:10]
                else:
                    file_hash = hash_file(filepath)
                    new_filename = f"{file_hash}"
                    new_original_filename = f"{new_filename}{ext.lower()}"
                    new_original_path = os.path.join(directory, new_original_filename)
                    if filepath != new_original_path:
                        os.rename(filepath, new_original_path)
                        filepath = new_original_path

                thumb_jpg_filename = f"{file_hash}_thumb.jpg"
                thumb_jpg_path = os.path.join(directory, thumb_jpg_filename)
                
                if not os.path.exists(thumb_jpg_path):
                    with Image.open(filepath) as img:
                        thumb_img = img.resize((512, 512), Image.LANCZOS)
                        thumb_img.convert('RGB').save(thumb_jpg_path, 'JPEG', quality=80)
                        print(f"Generated new thumbnail: {thumb_jpg_path}")

                full_jpg_filename = f"{file_hash}.jpg"
                full_jpg_path = os.path.join(directory, full_jpg_filename)
                if not os.path.exists(full_jpg_path):
                    if filepath != full_jpg_path:
                        shutil.copy2(filepath, full_jpg_path)

                frens_list.add(thumb_jpg_filename)
                print(f"Added to frens.txt: {thumb_jpg_filename}")

    with open(frens_txt_path, 'w') as f:
        for fren_name in sorted(frens_list):
            f.write(f"{fren_name}\n")
    print(f"Wrote {len(frens_list)} entries to {frens_txt_path}")

def process_scifi(directory):
    os.makedirs(directory, exist_ok=True)
    scifi_txt_path = os.path.join(directory, 'scifi.txt')
    scifi_list = read_existing_txt(scifi_txt_path)

    # Process new files
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext.lower() == '.jpg':
                if is_already_hashed(filename):
                    file_hash = filename[:10]
                else:
                    file_hash = hash_file(filepath)
                    new_filename = f"{file_hash}"
                    new_original_filename = f"{new_filename}{ext.lower()}"
                    new_original_path = os.path.join(directory, new_original_filename)
                    if filepath != new_original_path:
                        os.rename(filepath, new_original_path)
                        filepath = new_original_path

                thumb_jpg_filename = f"{file_hash}_thumb.jpg"
                thumb_jpg_path = os.path.join(directory, thumb_jpg_filename)
                
                if not os.path.exists(thumb_jpg_path):
                    with Image.open(filepath) as img:
                        thumb_img = img.resize((512, 512), Image.LANCZOS)
                        thumb_img.convert('RGB').save(thumb_jpg_path, 'JPEG', quality=80)
                        print(f"Generated new thumbnail: {thumb_jpg_path}")

                full_jpg_filename = f"{file_hash}.jpg"
                full_jpg_path = os.path.join(directory, full_jpg_filename)
                if not os.path.exists(full_jpg_path):
                    if filepath != full_jpg_path:
                        shutil.copy2(filepath, full_jpg_path)

                scifi_list.add(thumb_jpg_filename)
                print(f"Added to scifi.txt: {thumb_jpg_filename}")

    with open(scifi_txt_path, 'w') as f:
        for scifi_name in sorted(scifi_list):
            f.write(f"{scifi_name}\n")
    print(f"Wrote {len(scifi_list)} entries to {scifi_txt_path}")

def process_photos(directory):
    os.makedirs(directory, exist_ok=True)
    photos_txt_path = os.path.join(directory, 'photos.txt')
    photos_list = read_existing_txt(photos_txt_path)

    # Process new files
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.jpg', '.jpeg', '.png']:  # Added .png support
                if is_already_hashed(filename):
                    file_hash = filename[:10]
                else:
                    file_hash = hash_file(filepath)
                    new_filename = f"{file_hash}"
                    new_original_filename = f"{new_filename}{ext.lower()}"
                    new_original_path = os.path.join(directory, new_original_filename)
                    if filepath != new_original_path:
                        os.rename(filepath, new_original_path)
                        filepath = new_original_path

                thumb_jpg_filename = f"{file_hash}_thumb.jpg"
                thumb_jpg_path = os.path.join(directory, thumb_jpg_filename)
                
                if not os.path.exists(thumb_jpg_path):
                    with Image.open(filepath) as img:
                        thumb_img = img.resize((512, 512), Image.LANCZOS)
                        thumb_img.convert('RGB').save(thumb_jpg_path, 'JPEG', quality=80)
                        print(f"Generated new thumbnail: {thumb_jpg_path}")

                full_jpg_filename = f"{file_hash}.jpg"
                full_jpg_path = os.path.join(directory, full_jpg_filename)
                if not os.path.exists(full_jpg_path):
                    if ext.lower() == '.png':
                        with Image.open(filepath) as img:
                            img.convert('RGB').save(full_jpg_path, 'JPEG', quality=80)
                    else:
                        if filepath != full_jpg_path:
                            shutil.copy2(filepath, full_jpg_path)

                photos_list.add(thumb_jpg_filename)
                print(f"Added to photos.txt: {thumb_jpg_filename}")

    with open(photos_txt_path, 'w') as f:
        for photo_name in sorted(photos_list):
            f.write(f"{photo_name}\n")
    print(f"Wrote {len(photos_list)} entries to {photos_txt_path}")

# Directory paths
image_dir = os.path.join(os.getcwd(), "images")
video_dir = os.path.join(os.getcwd(), "videos")
frens_dir = os.path.join(os.getcwd(), "frens")
scifi_dir = os.path.join(os.getcwd(), "scifi")
photos_dir = os.path.join(os.getcwd(), "photos")

# Process everything
process_images(image_dir)
process_videos(video_dir)
process_frens(frens_dir)
process_scifi(scifi_dir)
process_photos(photos_dir)