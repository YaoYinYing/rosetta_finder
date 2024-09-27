import pytest
import os
import tempfile
import shutil
from contextlib import contextmanager

from rosetta_finder.utils import isolate

def test_isolate_creates_and_moves_files(tmp_path):
    """Test that files created in the isolated environment are moved to the target directory."""
    save_to = tmp_path / "final_directory"
    file_name = "test_file.txt"

    # Ensure save_to directory doesn't exist initially
    assert not os.path.exists(save_to)

    with isolate(save_to=str(save_to)) as _:
        # Create a file inside the isolated temporary directory
        with open(file_name, 'w') as f:
            f.write("This is a test file")

        # Check the file is created in the isolated directory (current working directory)
        assert os.path.exists(file_name)

    # After isolation, check that the file has been moved to the save_to directory
    moved_file_path = os.path.join(save_to, file_name)
    assert os.path.exists(moved_file_path)

    # Check the content of the moved file is the same as what was written
    with open(moved_file_path, 'r') as f:
        content = f.read()
    assert content == "This is a test file"

def test_isolate_changes_directory_back(tmp_path):
    """Test that the working directory is restored after isolation."""
    original_dir = os.getcwd()
    save_to = tmp_path / "final_directory"

    with isolate(save_to=str(save_to)) as _:
        # Change directory to temporary one
        assert os.getcwd() != original_dir  # Confirm we are in a different directory

    # After the context manager, the original directory should be restored
    assert os.getcwd() == original_dir

def test_isolate_with_base_dir(tmp_path):
    """Test that the base_dir parameter works properly."""
    base_dir = str(tmp_path / "base")
    os.makedirs(base_dir)  # Create the base directory

    save_to = tmp_path / "final_directory"

    with isolate(save_to=str(save_to), base_dir=base_dir) as _:
        # Ensure we are in a temporary directory inside the base_dir
        assert os.getcwd().startswith(base_dir)

    # After isolation, files should be moved to the save_to directory
    assert os.path.exists(save_to)
