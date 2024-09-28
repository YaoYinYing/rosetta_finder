import os

import pytest

from ..conftest import no_rosetta


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_app_supercharge():
    """
    Test the supercharge function with real parameters from Rosetta.
    """
    from rosetta_finder.app import supercharge

    pdb = "tests/data/3fap_hf3_A.pdb"
    supercharge(pdb, nproc=os.cpu_count())

