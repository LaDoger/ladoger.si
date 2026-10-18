#!/usr/bin/env python3
"""Add new media files to the site without touching anything already there.

Usage: python3 add_media.py [--pin] [--dry-run] [--no-upload] FILE...

Each file is copied (never moved) to the local, git-ignored images/<md5[:8]>.<ext>,
uploaded to Cloudflare R2 (bucket ladoger-art-media, served at
https://media.ladoger.art/images/<name>), then appended to images.txt and
optionally pinned.txt. Videos also get a first-frame .jpg thumbnail (ffmpeg),
which is uploaded too. Only images.txt / pinned.txt get committed to git.

Upload needs rclone plus R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY in the
environment (R2_ACCOUNT_ID and R2_BUCKET are optional overrides). A file is only
added to the list files after its upload succeeds.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(ROOT, 'images')
IMAGES_TXT = os.path.join(ROOT, 'images.txt')
PINNED_TXT = os.path.join(ROOT, 'pinned.txt')
VIDEO_EXTS = {'.mp4', '.mov', '.webm', '.mkv', '.avi'}

R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID', 'de6c863310eb0e7aab28675c3dae38a2')
R2_BUCKET = os.environ.get('R2_BUCKET', 'ladoger-art-media')
MEDIA_BASE = 'https://media.ladoger.art/'


def r2_env():
    key, secret = os.environ.get('R2_ACCESS_KEY_ID'), os.environ.get('R2_SECRET_ACCESS_KEY')
    if not key or not secret:
        raise RuntimeError('R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY not set')
    if not shutil.which('rclone'):
        raise RuntimeError('rclone not installed (https://rclone.org/install/)')
    env = dict(os.environ)
    env.update({
        'RCLONE_CONFIG_R2_TYPE': 's3',
        'RCLONE_CONFIG_R2_PROVIDER': 'Cloudflare',
        'RCLONE_CONFIG_R2_ENDPOINT': f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        'RCLONE_CONFIG_R2_ACCESS_KEY_ID': key,
        'RCLONE_CONFIG_R2_SECRET_ACCESS_KEY': secret,
        'RCLONE_CONFIG_R2_NO_CHECK_BUCKET': 'true',
    })
    return env


def upload_to_r2(local, key):
    """Upload local file to R2 at key (e.g. images/abc.jpg), verifying the MD5."""
    result = subprocess.run(
        ['rclone', 'copyto', local, f'r2:{R2_BUCKET}/{key}', '--checksum',
         '--s3-upload-cutoff', '5G',
         '--header-upload', 'Cache-Control: public, max-age=86400'],
        env=r2_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError('R2 upload failed: ' + result.stderr.strip()[-500:])


def md5_prefix(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:8]


def read_names(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def append_line(path, name):
    """Append name as a new line, adding a newline first if the file lacks one."""
    prefix = ''
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, 'rb') as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b'\n':
                prefix = '\n'
    with open(path, 'a', encoding='utf-8') as f:
        f.write(prefix + name + '\n')


def make_thumbnail(video, thumb):
    result = subprocess.run(
        ['ffmpeg', '-nostdin', '-loglevel', 'error', '-n',
         '-i', video, '-vframes', '1', thumb],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 or not os.path.exists(thumb):
        raise RuntimeError('ffmpeg failed: ' + result.stderr.strip())


def main():
    parser = argparse.ArgumentParser(description='Add media files to images/.')
    parser.add_argument('--pin', action='store_true', help='also add to pinned.txt')
    parser.add_argument('--dry-run', action='store_true', help='print actions, write nothing')
    parser.add_argument('--no-upload', action='store_true',
                        help='skip the R2 upload (lists are still updated; upload images/ yourself)')
    parser.add_argument('files', nargs='+', metavar='FILE')
    args = parser.parse_args()

    dry = args.dry_run
    os.makedirs(IMAGES_DIR, exist_ok=True)
    tag = '[dry-run] ' if dry else ''
    images = set(read_names(IMAGES_TXT))
    pinned = set(read_names(PINNED_TXT))
    added, duplicates, newly_pinned, errors = [], [], [], []

    for src in args.files:
        try:
            if not os.path.isfile(src):
                raise FileNotFoundError('not a file: ' + src)
            ext = os.path.splitext(src)[1].lower()
            if not ext:
                raise ValueError('no file extension: ' + src)
            name = md5_prefix(src) + ext
            target = os.path.join(IMAGES_DIR, name)

            if name in images:
                duplicates.append(name)
                print(f'{tag}DUPLICATE {src} -> {name} (already in images.txt, not copied)')
            else:
                if os.path.exists(target):
                    print(f'{tag}LOCAL images/{name} already exists (retrying upload)')
                else:
                    print(f'{tag}COPY {src} -> images/{name}')
                    if not dry:
                        shutil.copy2(src, target)

                to_upload = [name]
                if ext in VIDEO_EXTS:
                    thumb_name = os.path.splitext(name)[0] + '.jpg'
                    thumb = os.path.join(IMAGES_DIR, thumb_name)
                    to_upload.append(thumb_name)
                    if os.path.exists(thumb):
                        print(f'{tag}THUMB images/{thumb_name} already exists, skipping')
                    else:
                        print(f'{tag}THUMB images/{thumb_name} (first frame)')
                        if not dry:
                            make_thumbnail(target, thumb)

                for up in to_upload:
                    if args.no_upload:
                        print(f'{tag}SKIP UPLOAD images/{up} (--no-upload)')
                        continue
                    print(f'{tag}UPLOAD images/{up} -> {MEDIA_BASE}images/{up}')
                    if not dry:
                        upload_to_r2(os.path.join(IMAGES_DIR, up), f'images/{up}')

                print(f'{tag}APPEND {name} to images.txt')
                if not dry:
                    append_line(IMAGES_TXT, name)
                images.add(name)
                added.append(name)

            if args.pin:
                if name in pinned:
                    print(f'{tag}PIN {name} already in pinned.txt')
                else:
                    print(f'{tag}PIN append {name} to pinned.txt')
                    if not dry:
                        append_line(PINNED_TXT, name)
                    pinned.add(name)
                    newly_pinned.append(name)
        except Exception as e:
            errors.append(f'{src}: {e}')
            print(f'ERROR {src}: {e} (not added to images.txt)', file=sys.stderr)

    print()
    print(f'{tag}Summary: added {len(added)}, duplicates {len(duplicates)}, '
          f'pinned {len(newly_pinned)}, errors {len(errors)}')
    if added and not dry:
        print('Next: git add images.txt pinned.txt && git commit && git push (media is already on R2).')
    for err in errors:
        print(f'  error: {err}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
