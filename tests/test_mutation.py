import pytest
from rosetta_finder.common import Mutation, ProteinSequence, Chain, Mutant


# Test cases for the Mutation class


def test_mutation_creation():
    """
    Test that a Mutation object is created with the correct attributes.
    """
    mutation = Mutation(chain_id="A", position=123, wt_res="A", mut_res="B")

    assert mutation.chain_id == "A"
    assert mutation.position == 123
    assert mutation.wt_res == "A"
    assert mutation.mut_res == "B"


def test_mutation_str():
    """
    Test that the __str__ method returns the expected string format 'A123B'.
    """
    mutation = Mutation(chain_id="A", position=123, wt_res="A", mut_res="B")
    assert str(mutation) == "A123B"


def test_mutation_to_rosetta_format():
    """
    Test the to_rosetta_format method, with a sample jump index.
    """
    mutation = Mutation(chain_id="A", position=123, wt_res="A", mut_res="B")
    assert mutation.to_rosetta_format(jump_index=123) == "A 123 B"


# Test cases for the ProteinSequence class


def test_protein_sequence_creation():
    """
    Test that a ProteinSequence object is created and chains are added properly.
    """
    protein = ProteinSequence()
    protein.add_chain("A", "AAAAAAAAAA" * 10)  # Chain A with 100 residues
    protein.add_chain("B", "CCCCCCCCCC" * 5)  # Chain B with 50 residues

    assert len(protein.chains) == 2
    assert protein.get_sequence_by_chain("A") == "AAAAAAAAAA" * 10
    assert protein.get_sequence_by_chain("B") == "CCCCCCCCCC" * 5


def test_protein_sequence_jump_index():
    """
    Test the calculation of the jump index across chains in a ProteinSequence.
    """
    protein = ProteinSequence()
    protein.add_chain("A", "AAAAAAAAAA" * 10)  # 100 residues
    protein.add_chain("B", "CCCCCCCCCC" * 5)  # 50 residues

    # Test jump index for chain A
    assert protein.calculate_jump_index(chain_id="A", position=20) == 20

    # Test jump index for chain B
    assert protein.calculate_jump_index(chain_id="B", position=10) == 110  # Chain A has 100 residues


def test_protein_sequence_mutation_to_rosetta_format():
    """
    Test the mutation_to_rosetta_format method in the ProteinSequence class.
    """
    protein = ProteinSequence()
    protein.add_chain("A", "AAAAAAAAAA" * 10)  # 100 residues
    protein.add_chain("B", "CCCCCCCCCC" * 5)  # 50 residues

    mutation = Mutation(chain_id="B", position=10, wt_res="C", mut_res="D")
    rosetta_format = protein.mutation_to_rosetta_format(mutation)

    assert rosetta_format == "C 110 D"  # Chain A has 100 residues, so B10 becomes 110


# Test cases for the Mutant class


def test_mutant_creation():
    """
    Test that a Mutant object is created correctly with a ProteinSequence and mutations.
    """
    protein = ProteinSequence()
    protein.add_chain("A", "AAAAAAAAAA" * 10)
    protein.add_chain("B", "CCCCCCCCCC" * 5)

    mutation_1 = Mutation(chain_id="A", position=20, wt_res="A", mut_res="B")
    mutation_2 = Mutation(chain_id="B", position=10, wt_res="C", mut_res="D")

    mutant = Mutant(mutations=[mutation_1, mutation_2], protein_sequence=protein)

    assert len(mutant.mutations) == 2
    assert mutant.raw_mutant_id == "A20B_C10D"


def test_mutant_generate_rosetta_mutfile(tmp_path):
    """
    Test that the Mutant class generates the correct Rosetta mutfile format.
    """
    protein = ProteinSequence()
    protein.add_chain("A", "AAAAAAAAAA" * 10)  # 100 residues
    protein.add_chain("B", "CCCCCCCCCC" * 5)  # 50 residues

    mutation_1 = Mutation(chain_id="A", position=20, wt_res="A", mut_res="B")
    mutation_2 = Mutation(chain_id="B", position=10, wt_res="C", mut_res="D")

    mutant = Mutant(mutations=[mutation_1, mutation_2], protein_sequence=protein)

    # Use a temporary file to store the output
    mutfile_path = tmp_path / "mutfile.txt"
    mutant.generate_rosetta_mutfile(file_path=str(mutfile_path))

    # Check file contents
    with open(mutfile_path, "r") as f:
        contents = f.readlines()

    assert contents == ["A 20 B\n", "C 110 D\n"]  # Mutation A20B and C10D


if __name__ == "__main__":
    pytest.main()
