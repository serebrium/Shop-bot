import uuid
from pathlib import Path


IMAGE_DIR = Path("data/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_image_sync(image_data: bytes) -> str:
    """Сохраняет изображение синхронно и возвращает путь (str)."""
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = IMAGE_DIR / filename
    with open(filepath, "wb") as f:
        f.write(image_data)
    return str(filepath)


async def save_image(image_data: bytes) -> str:
    """Сохраняет изображение асинхронно и возвращает путь (str)."""
    # Для простоты используем синхронную запись, I/O здесь короткое
    return save_image_sync(image_data)


