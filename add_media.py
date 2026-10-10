#!/usr/bin/env python3
"""Add new media files to images/ without touching anything already there.

Usage: python3 add_media.py [--pin] [--dry-run] FILE...

Each file is copied (never moved) to images/<md5[:8]>.<ext>, appended to
images.txt, and optionally appended to pinned.txt. Videos also get a
first-frame .jpg thumbnail generated with ffmpeg.
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
    parser.add_argument('files', nargs='+', metavar='FILE')
    args = parser.parse_args()

    dry = args.dry_run
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

            if os.path.exists(target) or name in images:
                duplicates.append(name)
                print(f'{tag}DUPLICATE {src} -> {name} (already present, not copied)')
            else:
                print(f'{tag}COPY {src} -> images/{name}')
                if not dry:
                    shutil.copy2(src, target)

                if ext in VIDEO_EXTS:
                    thumb_name = os.path.splitext(name)[0] + '.jpg'
                    thumb = os.path.join(IMAGES_DIR, thumb_name)
                    if os.path.exists(thumb):
                        print(f'{tag}THUMB images/{thumb_name} already exists, skipping')
                    else:
                        print(f'{tag}THUMB images/{thumb_name} (first frame)')
                        if not dry:
                            try:
                                make_thumbnail(target, thumb)
                            except Exception as e:
                                errors.append(f'{src}: {e}')
                                print(f'ERROR {src}: {e}', file=sys.stderr)

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
            print(f'ERROR {src}: {e}', file=sys.stderr)

    print()
    print(f'{tag}Summary: added {len(added)}, duplicates {len(duplicates)}, '
          f'pinned {len(newly_pinned)}, errors {len(errors)}')
    for err in errors:
        print(f'  error: {err}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
