from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from databases import Database
    from types_aiobotocore_s3.client import S3Client

database: "Database"
s3_client: "S3Client"
