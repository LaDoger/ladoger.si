# SaylorPortraits

Source of https://ladoger.art (auto-mirrored to https://ladoger.si by `.github/workflows/mirror-ladoger-si.yml`).

## Where the media lives
Images, videos and audio are **not** in this repo. They live in Cloudflare R2
(bucket `ladoger-art-media`) and are served from **https://media.ladoger.art/** with the
same paths as before (`images/…`, `v1/…`, `refs/…`). The site code reads them via one
constant, `MEDIA_BASE`, in `index.html` (and in `v1/index.html`). `images/`, `refs/` and the
v1 media are in `.gitignore`. `404.html` sends old links like `ladoger.art/images/x.jpg`
to the same file on media.ladoger.art.

## How to add media
1. Install `rclone`, and set `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` (an R2 API token with write access to `ladoger-art-media`).
2. Run `python3 add_media.py [--pin] FILE...`. It names each file `<md5[:8]>.<ext>`, makes a first-frame `.jpg` thumbnail for videos, uploads everything to R2, and only then appends the names to `images.txt` (and `pinned.txt` with `--pin`).
3. Commit and push only `images.txt` / `pinned.txt`.

`formatter.py` is retired and refuses to run.
