
import pytest
from ..conftest import no_rosetta


@pytest.mark.integration
@pytest.mark.skipif(no_rosetta(), reason="No Rosetta Installed.")
def test_app_rosettaligand():
    from rosetta_finder.app.rosettaligand import main

    main()
