import logging
from typing import Any

from app import settings
from app import state


async def get_object_data(key: str) -> bytes | None:
    try:
        s3_object = await state.s3_client.get_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
        )
    except state.s3_client.exceptions.NoSuchKey:
        return None
    except Exception:
        logging.exception(
            "Unexpected error when fetching object data from S3",
            exc_info=True,
            extra={"object_key": key},
        )
        return None

    return await s3_object["Body"].read()


async def save_object_data(
    key: str,
    data: bytes,
    *,
    max_age: int | None = None,
) -> None:
    try:
        params: dict[str, Any] = {}
        if max_age is not None:
            params["CacheControl"] = f"max-age={max_age}"

        await state.s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
            Body=data,
            **params,
        )
    except Exception:
        logging.exception(
            "Unexpected error when saving object data from S3",
            exc_info=True,
            extra={"object_key": key, "data_size": len(data)},
        )
        return None


async def delete_object(key: str) -> None:
    try:
        await state.s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
        )
    except Exception:
        logging.warning(
            "Failed to delete object from S3",
            exc_info=True,
            extra={"object_key": key},
        )
        return None
