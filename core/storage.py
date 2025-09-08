from django.core.files.storage import FileSystemStorage
from django.conf import settings
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import os


class CompressedImageStorage(FileSystemStorage):
    """Custom storage for CKEditor uploads with auto image compression."""

    def _save(self, name, content):
        # Only process image files
        ext = os.path.splitext(name)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                img = Image.open(content)

                # Resize
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save to buffer
                buffer = BytesIO()
                img_format = "JPEG" if ext in [".jpg", ".jpeg"] else "PNG"
                img.save(buffer, format=img_format, quality=80, optimize=True)

                # Replace content with compressed version
                content = ContentFile(buffer.getvalue())
            except Exception as e:
                print(f"Image compression failed: {e}")

        return super()._save(name, content)
