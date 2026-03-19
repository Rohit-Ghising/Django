from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    S3-backed storage for media/ uploaded by the products app.
    """

    default_acl = None
    file_overwrite = False
    location = "media"
