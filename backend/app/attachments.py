"""Хранение картинок-вложений обращений на диске (volume /data).

Файлы лежат в папке `attachments` рядом с БД и отдаются только через защищённый
эндпоинт (проверка владельца тикета / админа). Имя файла генерируем сами (uuid) —
имени из браузера не доверяем, это защита от path traversal и коллизий.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

# Лимит размера одного вложения.
MAX_BYTES = 5 * 1024 * 1024  # 5 МБ

# Белый список типов (denylist для загрузок ненадёжен) → расширение файла.
ALLOWED_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class AttachmentError(ValueError):
    """Невалидное вложение (неподдерживаемый тип или превышен размер)."""


def attachments_dir(db_path: str) -> Path:
    """Папка вложений рядом с файлом БД (в Docker — внутри volume /data)."""
    return Path(db_path).resolve().parent / "attachments"


async def save_upload(file: UploadFile, *, db_path: str) -> tuple[str, str]:
    """Валидирует и сохраняет картинку. Возвращает (имя_файла, mime).

    Имя файла — uuid + расширение по mime; оригинальное имя из браузера
    игнорируется. Бросает AttachmentError при неверном типе/размере.
    """
    mime = (file.content_type or "").lower()
    ext = ALLOWED_MIME.get(mime)
    if ext is None:
        raise AttachmentError("поддерживаются только изображения JPEG, PNG или WebP")

    # Читаем на байт больше лимита, чтобы поймать превышение без полной загрузки.
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise AttachmentError("файл больше 5 МБ")
    if not data:
        raise AttachmentError("пустой файл")

    directory = attachments_dir(db_path)
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (directory / name).write_bytes(data)
    return name, mime


def resolve(name: str | None, *, db_path: str) -> Path | None:
    """Полный путь к существующему вложению по имени из БД, либо None.

    Принимаем только базовое имя файла (без разделителей пути) — защита от
    path traversal, даже если в БД попало что-то неожиданное.
    """
    if not name or name != Path(name).name:
        return None
    path = attachments_dir(db_path) / name
    return path if path.is_file() else None
