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


class UploadError(Exception):
    pass


def _allowed_extension(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def _upload_root() -> Path:
    return Path(current_app.root_path) / "static" / "uploads"


def save_image(file: FileStorage, subfolder: str = "general", max_width: int = 1800) -> str:
    if not file or not file.filename:
        raise UploadError("No file provided.")
    if not _allowed_extension(file.filename):
        raise UploadError("Unsupported file type. Use JPG, PNG, or WEBP.")
    safe_sub = secure_filename(subfolder or "general").lower() or "general"
    if safe_sub not in ALLOWED_SUBFOLDERS:
        raise UploadError("Invalid upload destination.")

    upload_root = _upload_root()
    target_dir = upload_root / safe_sub
    target_dir.mkdir(parents=True, exist_ok=True)

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
            raise UploadError("Unsupported image format.")
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
    except Exception as exc:  # noqa: BLE001
        if path.exists():
            path.unlink(missing_ok=True)
        raise UploadError("Invalid or corrupt image file.") from exc

    return f"uploads/{safe_sub}/{filename}".replace("\\", "/")


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
