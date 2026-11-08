"""
utils/storage.py — Persistent Image Storage for CivicSetu
Supports Cloudinary in production and local disk fallback in development.
"""

import os
import uuid
import re
import logging
from flask import current_app, url_for

logger = logging.getLogger(__name__)


def sanitize_error(err: Exception) -> str:
    """
    Produce a safe, diagnostic string for exceptions without leaking credentials,
    API secrets, tokens, or raw connection strings.
    """
    msg = str(err)
    if not msg:
        return type(err).__name__

    # Mask URLs with embedded credentials: scheme://<credentials>@<host>
    msg = re.sub(r'([a-zA-Z0-9_+.-]+://)[^@\s]+@', r'\1***:***@', msg)
    # Mask API key/secret/token patterns in key-value pairs or query strings
    msg = re.sub(
        r'(api_secret|api_key|secret|password|token)[\'\"]?\s*[:=]\s*[\'\"]?[^\'\"\s&,]+',
        r'\1=***',
        msg,
        flags=re.IGNORECASE
    )
    # Mask raw hex or alphanumeric secrets (length 24+)
    msg = re.sub(r'\b[0-9a-fA-F]{24,}\b', '***', msg)

    return f"{type(err).__name__}: {msg}"


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid or missing in production."""
    pass


class StorageUploadError(StorageError):
    """Raised when an image upload fails."""
    pass


def is_production_env() -> bool:
    """Detect if running in a production environment (Render or FLASK_ENV=production)."""
    return os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('RENDER'))


def is_cloudinary_configured() -> bool:
    """Check if Cloudinary environment variables are available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if os.environ.get('CLOUDINARY_URL'):
        return True
    return bool(
        os.environ.get('CLOUDINARY_CLOUD_NAME') and
        os.environ.get('CLOUDINARY_API_KEY') and
        os.environ.get('CLOUDINARY_API_SECRET')
    )


def _configure_cloudinary():
    """Configure Cloudinary using environment variables."""
    try:
        import cloudinary
    except ImportError as e:
        raise StorageConfigurationError("Cloudinary package is not installed.") from e

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    cld_url = os.environ.get('CLOUDINARY_URL')
    if cld_url:
        # Re-initialize Cloudinary configuration to load CLOUDINARY_URL from environment
        cloudinary.reset_config()
    else:
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )


def upload_complaint_image(file_storage, upload_folder=None) -> str:
    """
    Upload a complaint image to Cloudinary (in production or when configured)
    or to local storage (in development).

    Returns a storage reference string:
      - 'cloudinary:<public_id>' for Cloudinary
      - 'uploads/<filename>' for local disk storage

    Raises:
      - StorageConfigurationError if Cloudinary is missing in production.
      - StorageUploadError if upload fails.
    """
    if not file_storage or not file_storage.filename:
        raise StorageUploadError("No file provided for upload.")

    in_prod = is_production_env()
    cloudinary_available = is_cloudinary_configured()

    ext = file_storage.filename.rsplit('.', 1)[1].lower() if '.' in file_storage.filename else 'jpg'
    file_uuid = uuid.uuid4().hex

    # 1. Cloudinary upload path
    if cloudinary_available:
        try:
            _configure_cloudinary()
            import cloudinary.uploader

            # Rewind file pointer to ensure full read
            file_storage.seek(0)

            # Upload using random UUID public_id under civicsetu/complaints
            public_id = f"civicsetu/complaints/{file_uuid}"
            result = cloudinary.uploader.upload(
                file_storage,
                public_id=public_id,
                filename=file_storage.filename,
                resource_type="image",
                overwrite=False,
                unique_filename=False
            )
            returned_public_id = result.get('public_id', public_id)
            logger.info("Successfully uploaded image to Cloudinary: %s", returned_public_id)
            return f"cloudinary:{returned_public_id}"

        except Exception as err:
            safe_err = sanitize_error(err)
            logger.error("Cloudinary upload failed: %s", safe_err)
            # In production, NEVER silently fall back to local disk
            if in_prod:
                raise StorageUploadError(
                    f"Cloud storage upload failed ({safe_err}). Please try again."
                ) from err
            # In development, fall through to local fallback with a log
            logger.warning("Development mode: Falling back to local disk storage after Cloudinary error [%s].", safe_err)

    # 2. Production check: If Cloudinary is not configured in production, fail explicitly
    if in_prod:
        raise StorageConfigurationError(
            "Cloudinary credentials are required in production environments but not configured."
        )

    # 3. Local disk fallback (development only)
    folder = upload_folder or current_app.config.get('UPLOAD_FOLDER')
    if not folder:
        raise StorageConfigurationError("Local upload folder is not configured.")

    os.makedirs(folder, exist_ok=True)
    filename = f"{file_uuid}.{ext}"
    save_path = os.path.join(folder, filename)

    file_storage.seek(0)
    file_storage.save(save_path)
    logger.info("Saved image to local storage: %s", filename)
    return f"uploads/{filename}"


def delete_complaint_image(image_ref: str) -> bool:
    """
    Delete an uploaded image.
    Used for compensation/cleanup if an associated database transaction fails.
    """
    if not image_ref:
        return False

    if image_ref.startswith('cloudinary:'):
        public_id = image_ref[len('cloudinary:'):]
        try:
            _configure_cloudinary()
            import cloudinary.uploader
            res = cloudinary.uploader.destroy(public_id, resource_type="image")
            logger.info("Deleted Cloudinary image %s: %s", public_id, res.get('result'))
            return res.get('result') == 'ok'
        except Exception as e:
            logger.warning("Failed to delete Cloudinary image %s [%s]", public_id, sanitize_error(e))
            return False

    elif image_ref.startswith('uploads/'):
        folder = current_app.config.get('UPLOAD_FOLDER') if current_app else None
        if folder:
            filename = os.path.basename(image_ref)
            local_path = os.path.join(folder, filename)
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    logger.info("Removed local file: %s", local_path)
                    return True
                except OSError as e:
                    logger.warning("Failed to remove local file [%s]", type(e).__name__)
        return False

    return False


def resolve_image_url(image_ref: str) -> str:
    """
    Resolve a database image reference into a browser-accessible URL.
    Handles:
      - 'cloudinary:<public_id>' -> Cloudinary CDN URL (optimized)
      - 'http://' or 'https://'  -> Raw URL (external)
      - 'uploads/<filename>'     -> Local static file URL via url_for('static', ...)
    """
    if not image_ref:
        return None

    if image_ref.startswith('cloudinary:'):
        public_id = image_ref[len('cloudinary:'):]
        try:
            _configure_cloudinary()
            import cloudinary
            import cloudinary.utils

            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
            if not cloud_name and os.environ.get('CLOUDINARY_URL'):
                m = re.search(r'@([^/?]+)', os.environ.get('CLOUDINARY_URL', ''))
                if m:
                    cloud_name = m.group(1)

            cld_url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                cloud_name=cloud_name or 'civicsetu',
                secure=True,
                fetch_format='auto',
                quality='auto'
            )
            return cld_url
        except Exception as e:
            logger.error("Failed to build Cloudinary URL for %s [%s]", public_id, sanitize_error(e))
            return f"https://res.cloudinary.com/civicsetu/image/upload/{public_id}"

    if image_ref.startswith(('http://', 'https://')):
        return image_ref

    # Local file
    try:
        return url_for('static', filename=image_ref)
    except RuntimeError:
        return f"/static/{image_ref}"
