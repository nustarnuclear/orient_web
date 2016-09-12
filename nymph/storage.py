from django.core.files.storage import FileSystemStorage
import platform


def get_file_root():
    system = platform.system()
    if system == "Windows":
        location = "D:\\orient\\nymph"
    elif system == "Linux":
        location = "/orient/nymph"
    return location


class NymphStorage(FileSystemStorage):
    """
    Returns same name for existing file and deletes existing file on save.
    """

    def __init__(self):
        location = get_file_root()
        base_url = "/orient/nymph"
        return super().__init__(location=location, base_url=base_url)
