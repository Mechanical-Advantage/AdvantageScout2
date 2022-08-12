import os


def get_absolute_path(*path):
    """Returns the absolute path based on a path relative to this folder."""
    joined_path = os.path.dirname(__file__)
    for item in path:
        joined_path = os.path.join(joined_path, item)
    return os.path.abspath(joined_path)
