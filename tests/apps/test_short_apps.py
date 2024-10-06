import os
import pytest
from ..conftest import no_rosetta


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
@pytest.mark.parametrize("num_mut", [1, 2])
def test_app_mutate_relax(num_mut):
    from RosettaPy.app.mutate_relax import main

    main(num_mut)


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_app_rosettaligand():
    from RosettaPy.app.rosettaligand import main

    main()


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_app_supercharge():
    """
    Test the supercharge function with real parameters from Rosetta.
    """
    from RosettaPy.app import supercharge

    pdb = "tests/data/3fap_hf3_A.pdb"
    supercharge(pdb, nproc=os.cpu_count())


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
@pytest.mark.parametrize("dualspace", [True, False])
def test_app_fastrelax(dualspace):
    from RosettaPy.app.fastrelax import main

    main(dualspace)
