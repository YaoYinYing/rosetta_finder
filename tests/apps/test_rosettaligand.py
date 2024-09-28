
import pytest
from ..conftest import no_rosetta,dockerized_rosetta



@pytest.mark.skipif(not dockerized_rosetta(), reason="No need to run this test in non-Dockerized Rosetta.")
@pytest.mark.integration
def test_app_rosettaligand():
    from rosetta_finder.app.rosettaligand import main

    main()
