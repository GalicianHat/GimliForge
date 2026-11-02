"""Validated, portable image evidence stored with each audit project."""
from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path

from .gimliforge import InputError

MAX_IMAGES_PER_FINDING = 5
MAX_IMAGE_BYTES = 3_000_000
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg"}


def validate_images(value, identifier):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_IMAGES_PER_FINDING:
        raise InputError(f"{identifier}: máximo {MAX_IMAGES_PER_FINDING} imágenes por hallazgo")
    images = []
    for image in value:
        if not isinstance(image, dict):
            raise InputError(f"{identifier}: imagen no válida")
        mime = image.get("mime")
        data = image.get("data")
        name = image.get("nombre", "")
        caption = image.get("leyenda", "")
        if mime not in IMAGE_TYPES or not isinstance(data, str) or len(data) > 4_100_000:
            raise InputError(f"{identifier}: use PNG o JPEG de hasta 3 MB")
        if not isinstance(name, str) or len(name) > 150 or not isinstance(caption, str) or len(caption) > 300:
            raise InputError(f"{identifier}: nombre o leyenda de imagen demasiado largo")
        try:
            raw = base64.b64decode(data, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise InputError(f"{identifier}: imagen codificada incorrectamente") from exc
        if not 0 < len(raw) <= MAX_IMAGE_BYTES:
            raise InputError(f"{identifier}: la imagen supera 3 MB")
        if mime == "image/png" and not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise InputError(f"{identifier}: el archivo no es PNG")
        if mime == "image/jpeg" and not raw.startswith(b"\xff\xd8\xff"):
            raise InputError(f"{identifier}: el archivo no es JPEG")
        images.append({"nombre": name.strip(), "leyenda": caption.strip(), "mime": mime, "data": data})
    return images


def image_name(identifier, index, mime):
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12]
    return f"evidencia_{digest}_{index:02d}{IMAGE_TYPES[mime]}"


def iter_images(findings):
    for finding in findings:
        for index, image in enumerate(finding.get("imagenes", []), 1):
            yield f"evidencias/{image_name(finding['id'], index, image['mime'])}", base64.b64decode(image["data"])


def write_images(root: Path, findings):
    for name, raw in iter_images(findings):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
