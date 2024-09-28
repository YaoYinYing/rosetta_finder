import os

import pytest

from ..conftest import no_rosetta,dockerized_rosetta



@pytest.mark.skipif(not dockerized_rosetta(), reason="No need to run this test in non-Dockerized Rosetta.")
@pytest.mark.integration
def test_app_supercharge():
    """
    Test the supercharge function with real parameters from Rosetta.
    """
    from rosetta_finder.app import supercharge

    pdb = "tests/data/3fap_hf3_A.pdb"
    supercharge(pdb, nproc=os.cpu_count())

