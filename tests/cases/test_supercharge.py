import os

from rosetta_finder.app import supercharge
import pytest
import shutil
import warnings


def no_rosetta():
    import subprocess

    result = subprocess.run(
        ["whichrosetta", "rosetta_scripts"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    # Check that the command was successful
    has_rosetta_installed = "rosetta_scripts" in result.stdout
    warnings.warn(UserWarning(f"Rosetta Installed: {has_rosetta_installed} - {result.stdout}"))
    return not has_rosetta_installed


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_app_supercharge():
    """
    Test the supercharge function with real parameters from Rosetta.
    """
    pdb = "tests/data/3fap_hf3_A.pdb"
    abs_target_charge = 20

    instance = os.path.basename(pdb)[:-4]

    # Ensure the function runs without exceptions
    try:
        supercharge(pdb, abs_target_charge=abs_target_charge)
    except Exception as e:
        pytest.fail(f"supercharge raised an exception: {e}")

    # Verify that the output files were created as expected

    scorefiles = [f for f in os.listdir("tests/outputs/test_supercharge/all") if f.startswith(instance)]

    assert len(scorefiles) > 0

    # assert len(scorefiles) == len(expect_total_jobs)

    assert os.path.isfile("resfile_output_Rsc")

    if os.path.isfile("resfile_output_Rsc"):
        os.remove("resfile_output_Rsc")
    if os.path.isdir("tests/outputs/test_supercharge"):
        shutil.rmtree("tests/outputs/test_supercharge")
