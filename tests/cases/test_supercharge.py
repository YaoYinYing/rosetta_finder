import os
from rosetta_finder.app import supercharge
import pytest
import shutil


@pytest.mark.integration
def test_supercharge():
    """
    Test the supercharge function with real parameters from Rosetta.
    """
    pdb = "tests/data/3fap_hf3_A.pdb"
    abs_target_charge = 20

    instance = os.path.basename(pdb)[:-4]

    expect_total_jobs = [x for x in range(-abs_target_charge, abs_target_charge, 2)]

    # Ensure the function runs without exceptions
    try:
        supercharge(pdb, abs_target_charge=abs_target_charge)
    except Exception as e:
        pytest.fail(f"supercharge raised an exception: {e}")

    # Verify that the output files were created as expected

    scorefiles = [f for f in os.listdir("tests/outputs/test_supercharge/scorefile") if f.startswith(instance)]

    assert len(scorefiles) > 0

    # assert len(scorefiles) == len(expect_total_jobs)

    assert os.path.isfile("resfile_output_Rsc")

    if os.path.isfile("resfile_output_Rsc"):
        os.remove("resfile_output_Rsc")
    if os.path.isdir("tests/outputs/test_supercharge"):
        shutil.rmtree("tests/outputs/test_supercharge")
