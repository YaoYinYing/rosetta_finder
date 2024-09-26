import os
from rosetta_finder import RosettaEnergyUnitAnalyser, Rosetta
from rosetta_finder.app.utils import PDBProcessor
from rosetta_finder.app import PROSS
import pytest
import shutil
import warnings

from ..conftest import no_rosetta


import os
from unittest.mock import patch, MagicMock


@pytest.fixture
def pross_instance():
    """Fixture for creating a PROSS instance."""
    return PROSS(pdb="tests/data/3fap_hf3_A.pdb", pssm="tests/data/3fap_hf3_A_ascii_mtx_file")


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_pross_initialization(pross_instance):
    """Test the initialization of PROSS class."""
    assert pross_instance.pdb == "tests/data/3fap_hf3_A.pdb"
    assert pross_instance.pssm == "tests/data/3fap_hf3_A_ascii_mtx_file"
    assert pross_instance.save_dir == "tests/outputs"
    assert pross_instance.job_id == "pross"
    assert pross_instance.res_to_fix == "1A"
    assert pross_instance.seq_len == 107


@patch("os.makedirs")
@patch("os.path.basename", return_value="3fap_hf3_A.pdb")
@patch("rosetta_finder.app.utils.PDBProcessor.convert_pdb_to_constraints", return_value=200)
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_pross_post_init(mock_convert, mock_basename, mock_makedirs, pross_instance):
    """Test the __post_init__ method of the PROSS class."""
    pross_instance.__post_init__()

    mock_basename.assert_called_once_with("tests/data/3fap_hf3_A.pdb")
    mock_makedirs.assert_called_once_with(os.path.join(pross_instance.save_dir, pross_instance.job_id), exist_ok=True)
    mock_convert.assert_called_once_with(pross_instance.pdb, pross_instance.CA_constraints)
    assert pross_instance.instance == "3fap_hf3_A"
    assert pross_instance.CA_constraints == os.path.join(
        pross_instance.save_dir, pross_instance.job_id, "3fap_hf3_A_bbCA.cst"
    )
    assert pross_instance.seq_len == 107


@patch("rosetta_finder.Rosetta.run")
@patch("rosetta_finder.RosettaEnergyUnitAnalyser")
@patch("os.path.isfile", return_value=True)
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_refine(mock_isfile, mock_analyser, mock_rosetta_run, pross_instance):
    """Test the refine method of PROSS class."""
    mock_analyser.return_value.best_decoy = {"decoy": "best_decoy", "score": -100.0}
    pross_instance.refine(nstruct=10)

    mock_rosetta_run.assert_called_once()
    mock_isfile.assert_called_once_with(
        os.path.join(pross_instance.save_dir, pross_instance.job_id, "refinement", "best_decoy.pdb")
    )
    assert os.path.abspath(os.path.join(pross_instance.save_dir, pross_instance.job_id, "refinement", "best_decoy.pdb"))


@patch("rosetta_finder.Rosetta.run")
@patch("os.path.isfile", side_effect=[False, False, False, False, False, False, False, False])
@patch("os.makedirs")
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_filterscan_without_existing_files(mock_makedirs, mock_isfile, mock_rosetta_run, pross_instance):
    """Test filterscan method when no existing filter scan files are present."""
    refined_pdb = "tests/outputs/pross/refined_3fap_hf3_A.pdb"
    pross_instance.filterscan(refined_pdb)

    mock_makedirs.assert_called()
    mock_rosetta_run.assert_called_once()


@patch("rosetta_finder.Rosetta.run")
@patch("os.path.isfile", return_value=True)
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_filterscan_with_existing_files(mock_isfile, mock_rosetta_run, pross_instance):
    """Test filterscan method when all filter scan files already exist."""
    refined_pdb = "tests/outputs/pross/refined_3fap_hf3_A.pdb"
    resfiles = pross_instance.filterscan(refined_pdb)

    mock_isfile.assert_called()
    mock_rosetta_run.assert_not_called()  # Should skip Rosetta execution
    assert len(resfiles) == len(pross_instance.filter_thresholds)  # Check that all resfiles are returned


@patch("os.path.isfile", return_value=True)
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_merge_resfiles(mock_isfile, pross_instance):
    """Test the merge_resfiles method."""
    filterscan_dir = "tests/outputs/pross/filterscan"
    resfiles = pross_instance.merge_resfiles(filterscan_dir, 10)

    mock_isfile.assert_called()
    assert len(resfiles) == len(pross_instance.filter_thresholds)


@patch("rosetta_finder.Rosetta.run")
@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_design(mock_rosetta_run, pross_instance):
    """Test the design method of the PROSS class."""
    filters = [f"designable_aa_resfile.{i}" for i in pross_instance.filter_thresholds]
    refined_pdb = "tests/outputs/pross/refined_3fap_hf3_A.pdb"
    pross_instance.design(filters, refined_pdb)

    mock_rosetta_run.assert_called_once()
