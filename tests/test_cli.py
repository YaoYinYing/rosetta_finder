import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Assuming main and RosettaFinder are imported from the target module
from rosetta_finder import main, RosettaFinder
from tests.conftest import github_rosetta_test


@pytest.fixture
def mock_shutil_which():
    """Fixture to mock shutil.which for testing."""
    with patch('shutil.which') as mock_which:
        yield mock_which


@pytest.fixture
def mock_os_path_isfile():
    """Fixture to mock os.path.isfile for testing."""
    with patch('os.path.isfile') as mock_isfile:
        yield mock_isfile


@pytest.fixture
def mock_RosettaFinder():
    """Fixture to mock the RosettaFinder class."""
    with patch('rosetta_finder.RosettaFinder') as mock_finder_class:
        mock_finder = MagicMock()
        mock_finder_class.return_value = mock_finder
        yield mock_finder


def test_main_binary_in_path(mock_shutil_which, mock_os_path_isfile):
    """Test case where the binary is found in system's PATH."""
    # Setup
    sys.argv = ['whichrosetta', 'relax']
    mock_shutil_which.return_value = '/usr/local/bin/relax.static.linuxgccrelease'
    mock_os_path_isfile.return_value = True

    # Test
    with patch('builtins.print') as mocked_print:
        main()

    # Assert
    mock_shutil_which.assert_called_once_with('relax')
    mock_os_path_isfile.assert_called_once_with('/usr/local/bin/relax.static.linuxgccrelease')
    mocked_print.assert_called_once_with('/usr/local/bin/relax.static.linuxgccrelease')


@pytest.mark.skipif(github_rosetta_test(), reason="No need to run this test in Dockerized Rosetta.")
def test_main_binary_not_found(mock_shutil_which, mock_os_path_isfile, mock_RosettaFinder):
    """Test case where the binary is neither in the PATH nor found by RosettaFinder."""
    # Setup


    sys.argv = ['whichrosetta', 'relax']
    mock_shutil_which.return_value = None
    mock_RosettaFinder.find_binary.return_value.full_path = ''
    mock_os_path_isfile.return_value = False

    # Test & Assert
    with pytest.raises(FileNotFoundError, match=" does not exist."):
        main()

    mock_shutil_which.assert_called()
