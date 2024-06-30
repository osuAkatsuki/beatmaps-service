import logging

from app import settings
from app import state


async def get_object_data(key: str) -> bytes | None:
    try:
        s3_object = await state.s3_client.get_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
        )
    except Exception:
        logging.warning(
            "Failed to get object data from S3",
            exc_info=True,
            extra={"object_key": key},
        )
        return None

    return await s3_object["Body"].read()


async def save_object_data(key: str, data: bytes) -> None:
    try:
        await state.s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
            Body=data,
        )
    except Exception:
        logging.warning(
            "Failed to save object data to S3",
            exc_info=True,
            extra={"object_key": key},
        )
        return None
