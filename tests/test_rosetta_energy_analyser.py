import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from rosetta_finder import RosettaEnergyUnitAnalyser  # Replace with the actual module name


sample_score_file = "tests/data/score.sc"
best_decoy = {"idx": 2, "score": -388.465, "decoy": "3fap_hf3_A_0003"}
best_decoy_cat = {"idx": 5, "score": -788.235, "decoy": "3fap_hf3_A_0006"}

# Test a non-existing score file


# Test cases
class TestRosettaEnergyUnitAnalyser:
    def test_single_score_file(self):
        analyser = RosettaEnergyUnitAnalyser(score_file=sample_score_file)
        assert analyser.best_decoy == best_decoy

    def test_multiple_score_files(self):
        analyser = RosettaEnergyUnitAnalyser(score_file=os.path.dirname(sample_score_file))
        assert analyser.best_decoy == best_decoy_cat

    def test_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            RosettaEnergyUnitAnalyser(score_file=os.path.join(sample_score_file, "non_existing_file.sc"))

    def test_missing_score_term(self):
        with pytest.raises(ValueError):
            RosettaEnergyUnitAnalyser(score_file=sample_score_file, score_term="missing_score_term")


# Run pytest to execute tests
if __name__ == "__main__":
    pytest.main()
