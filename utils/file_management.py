"""Utility functions to handle downloaded files."""

import glob
import os
import pathlib
import re
from hashlib import md5


def get_next_name(file_path: str) -> str:
    """
    Get next available name to download file.

    Parameters
    ----------
    file_path: str
        Absolute path of the file for which next available name to
        be generated.

    Returns
    -------
    str
        Absolute path of the next available name for the file.
    """
    posix_path = pathlib.Path(file_path)
    counter: int = 1
    new_file_name: str = os.path.join("{0}", "{1}-copy{2}{3}")
    while os.path.isfile(
        new_file_name.format(
            posix_path.parent,
            posix_path.stem,
            counter,
            "".join(posix_path.suffixes),
        )
    ):
        counter += 1
    return new_file_name.format(
        posix_path.parent,
        posix_path.stem,
        counter,
        "".join(posix_path.suffixes),
    )


def manage_duplicate_file(file_path: str) -> str:
    """
    Check if a file is duplicate.

    Compare the md5 of files with copy name pattern
    and remove if the md5 hash is same.

    Parameters
    ----------
    file_path: str
        Absolute path of the file for which duplicates needs to
        be managed.

    Returns
    -------
    str
        Absolute path of the duplicate managed file.
    """
    # pylint: disable = R1732
    posix_path = pathlib.Path(file_path)
    base_stem: str = re.sub(r"-copy\d+$", "", posix_path.stem)
    ext: str = "".join(posix_path.suffixes)
    parent_dir = posix_path.parent
    pattern = re.compile(rf"^{re.escape(base_stem)}(-copy\d+)?{re.escape(ext)}$")

    if not parent_dir.is_dir() or not os.path.isfile(file_path):
        return file_path

    try:
        current_size = os.path.getsize(file_path)
    except OSError:
        return file_path

    old_files = []
    try:
        for entry in os.scandir(parent_dir):
            if entry.is_file() and pattern.match(entry.name):
                try:
                    if not os.path.samefile(entry.path, file_path):
                        old_files.append(entry.path)
                except OSError:
                    pass
    except OSError:
        return file_path

    # Sort old files so base file or lowest copy index is preferred as canonical
    old_files.sort()

    def _file_md5(p: str) -> str:
        hasher = md5()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    current_file_md5 = None
    for old_file_path in old_files:
        try:
            old_size = os.path.getsize(old_file_path)
            # Fast check: different sizes can NEVER have the same hash
            if old_size != current_size:
                continue
            if current_file_md5 is None:
                current_file_md5 = _file_md5(file_path)
            if current_file_md5 == _file_md5(old_file_path):
                os.remove(file_path)
                return old_file_path
        except OSError:
            continue

    return file_path

