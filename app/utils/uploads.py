"""Secure image upload helpers."""

from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path

from flask import current_app
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_SUBFOLDERS = {
    "general",
    "tours",
    "destinations",
    "blog",
    "gallery",
    "services",
    "partners",
    "brand",
}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


class UploadError(Exception):
    pass


def has_upload(file_storage) -> bool:
    """True only when the browser sent a real file (empty FileStorage is truthy)."""
    return bool(file_storage and getattr(file_storage, "filename", None))


def media_kind(filename: str | None) -> str | None:
    """Return 'image', 'video', or None from a filename extension."""
    if not filename or "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    return None


def _allowed_extension(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def _upload_root() -> Path:
    return Path(current_app.root_path) / "static" / "uploads"


def _ensure_upload_dir(subfolder: str) -> Path:
    safe_sub = secure_filename(subfolder or "general").lower() or "general"
    if safe_sub not in ALLOWED_SUBFOLDERS:
        raise UploadError("Invalid upload destination.")
    target_dir = _upload_root() / safe_sub
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UploadError(
            "Upload folder is not writable. On Docker, ensure the uploads volume "
            "is owned by the app user (redeploy with the latest entrypoint)."
        ) from exc
    return target_dir


def save_image(file: FileStorage, subfolder: str = "general", max_width: int = 1800) -> str:
    if not file or not file.filename:
        raise UploadError("No file provided.")
    if not _allowed_extension(file.filename):
        raise UploadError("Unsupported file type. Use JPG, PNG, or WEBP.")

    target_dir = _ensure_upload_dir(subfolder)
    safe_sub = target_dir.name

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    filename = f"{uuid.uuid4().hex}_{secrets.token_hex(4)}.{ext}"
    path = target_dir / filename

    try:
        image = Image.open(file.stream)
        image.verify()
        file.stream.seek(0)
        image = Image.open(file.stream)
        fmt = (image.format or "").upper()
        if fmt not in ALLOWED_PIL_FORMATS:
            raise UploadError("Unsupported image format. Use JPG, PNG, or WEBP.")
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        # Basic decompression bomb guard
        if image.width * image.height > 40_000_000:
            raise UploadError("Image dimensions are too large.")
        if image.width > max_width:
            ratio = max_width / float(image.width)
            image = image.resize((max_width, int(image.height * ratio)), Image.Resampling.LANCZOS)
        save_kwargs = {"optimize": True}
        if ext in ("jpg", "jpeg"):
            save_kwargs["quality"] = 85
            if image.mode == "RGBA":
                image = image.convert("RGB")
        image.save(path, **save_kwargs)
    except UploadError:
        if path.exists():
            path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        if path.exists():
            path.unlink(missing_ok=True)
        raise UploadError(
            "Could not write the image file. Check upload folder permissions."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        if path.exists():
            path.unlink(missing_ok=True)
        raise UploadError("Invalid or corrupt image file.") from exc

    return f"uploads/{safe_sub}/{filename}".replace("\\", "/")


def save_video(file: FileStorage, subfolder: str = "gallery") -> str:
    """Save an MP4/WebM/MOV video under static/uploads/<subfolder>/."""
    if not file or not file.filename:
        raise UploadError("No file provided.")
    kind = media_kind(file.filename)
    if kind != "video":
        raise UploadError("Unsupported video type. Use MP4, WebM, or MOV.")

    max_bytes = int(current_app.config.get("MAX_VIDEO_BYTES", 64 * 1024 * 1024))
    # Prefer content_length when available; otherwise stream-check while writing.
    if file.content_length and file.content_length > max_bytes:
        raise UploadError(f"Video is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")

    target_dir = _ensure_upload_dir(subfolder)
    safe_sub = target_dir.name
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}_{secrets.token_hex(4)}.{ext}"
    path = target_dir / filename

    try:
        written = 0
        chunk_size = 1024 * 1024
        with open(path, "wb") as out:
            while True:
                chunk = file.stream.read(chunk_size)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise UploadError(
                        f"Video is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
                    )
                out.write(chunk)
        if written == 0:
            raise UploadError("Empty video file.")
        # Light container sniff (ISO BMFF / WebM)
        with open(path, "rb") as fh:
            header = fh.read(12)
        if ext in ("mp4", "mov"):
            if len(header) < 8 or header[4:8] != b"ftyp":
                raise UploadError("Invalid or corrupt video file.")
        elif ext == "webm":
            if not header.startswith(b"\x1a\x45\xdf\xa3"):
                raise UploadError("Invalid or corrupt video file.")
    except UploadError:
        if path.exists():
            path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        if path.exists():
            path.unlink(missing_ok=True)
        raise UploadError(
            "Could not write the video file. Check upload folder permissions."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        if path.exists():
            path.unlink(missing_ok=True)
        raise UploadError("Invalid or corrupt video file.") from exc

    return f"uploads/{safe_sub}/{filename}".replace("\\", "/")


def save_gallery_media(file: FileStorage) -> tuple[str, str]:
    """Save an image or video for the gallery. Returns (relative_path, media_type)."""
    kind = media_kind(file.filename if file else None)
    if kind == "image":
        return save_image(file, "gallery"), "image"
    if kind == "video":
        return save_video(file, "gallery"), "video"
    raise UploadError("Unsupported file type. Use JPG, PNG, WEBP, MP4, WebM, or MOV.")


def delete_upload(relative_path: str | None) -> None:
    if not relative_path:
        return
    if ".." in relative_path.replace("\\", "/") or relative_path.startswith(("/", "\\")):
        return

    upload_root = _upload_root().resolve()
    candidate = (Path(current_app.root_path) / "static" / relative_path).resolve()
    try:
        candidate.relative_to(upload_root)
    except ValueError:
        return
    if candidate.exists() and candidate.is_file():
        try:
            os.remove(candidate)
        except OSError:
            pass
