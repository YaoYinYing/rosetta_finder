from dataclasses import dataclass, field
from typing import List
import os
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB import Polypeptide


@dataclass
class Mutation:
    chain_id: str  # Chain ID of the mutation
    position: int  # Position within the chain (1-based index)
    wt_res: str  # Wild-type residue (original amino acid)
    mut_res: str  # Mutated residue (new amino acid)

    def __str__(self) -> str:
        """
        String representation of the mutation in the format 'A123B',
        where A is the wild-type residue, 123 is the position, and B is the mutated residue.
        """
        return f"{self.wt_res}{self.position}{self.mut_res}"

    def to_rosetta_format(self, jump_index: int) -> str:
        """
        Converts the mutation to Rosetta mutfile format with the jump index ('A 123 B').
        The jump index is the global residue index across all chains.
        """
        return f"{self.wt_res} {jump_index} {self.mut_res}"


@dataclass
class Chain:
    chain_id: str  # Chain ID (e.g., 'A', 'B', etc.)
    sequence: str  # Amino acid sequence of the chain

    def length(self) -> int:
        """
        Returns the length of the chain sequence.
        """
        return len(self.sequence)


@dataclass
class ProteinSequence:
    chains: List[Chain] = field(default_factory=list)

    def add_chain(self, chain_id: str, sequence: str):
        """
        Adds a new chain to the protein sequence.

        Args:
            chain_id (str): Chain ID (e.g., 'A', 'B', etc.)
            sequence (str): Amino acid sequence for the chain.
        """
        self.chains.append(Chain(chain_id=chain_id, sequence=sequence))

    def get_sequence_by_chain(self, chain_id: str) -> str:
        """
        Retrieves the sequence for a given chain ID.

        Args:
            chain_id (str): Chain ID (e.g., 'A', 'B').

        Returns:
            str: The amino acid sequence of the specified chain.

        Raises:
            ValueError: If the chain ID is not found.
        """
        for chain in self.chains:
            if chain.chain_id == chain_id:
                return chain.sequence
        raise ValueError(f"Chain {chain_id} not found in the protein sequence.")

    def calculate_jump_index(self, chain_id: str, position: int) -> int:
        """
        Calculate the jump residue index across all chains for the given chain_id and position.
        The jump index is a 1-based index across all chains in the protein sequence.

        Args:
            chain_id (str): The chain ID where the mutation occurs.
            position (int): The position within the chain (1-based index).

        Returns:
            int: The jump index across all chains.
        """
        jump_index = 0
        for chain in self.chains:
            if chain.chain_id == chain_id:
                jump_index += position
                break
            else:
                jump_index += chain.length()  # Add the length of the previous chains
        return jump_index

    def mutation_to_rosetta_format(self, mutation: Mutation) -> str:
        """
        Converts a Mutation object to the Rosetta mutfile format including jump index.

        Args:
            mutation (Mutation): The mutation object to convert.

        Returns:
            str: The Rosetta format string with the calculated jump index.
        """
        jump_index = self.calculate_jump_index(mutation.chain_id, mutation.position)
        return mutation.to_rosetta_format(jump_index)


@dataclass
class Mutant:
    mutations: List[Mutation]  # List of Mutation objects representing mutations
    protein_sequence: ProteinSequence  # ProteinSequence object to handle chain sequences
    _mutant_score: float = field(default_factory=float)
    _mutant_description: str = ""
    _pdb_fp: str = ""
    _mutant_id: str = ""
    _wt_score: float = 0.0

    def __post_init__(self):
        """
        This method is automatically called after the initialization of the instance.
        It ensures the list of mutations is valid and the protein sequence is set.
        """
        self.validate_mutations()

    def validate_mutations(self):
        """
        Validates the structure of the mutation list to ensure it's not empty and
        each element is a `Mutation` instance.
        """
        if not self.mutations:
            raise ValueError("Mutation list cannot be empty.")
        if not all(isinstance(mutation, Mutation) for mutation in self.mutations):
            raise TypeError("All elements in mutations must be instances of the Mutation class.")

    def generate_rosetta_mutfile(self, file_path: str):
        """
        Saves all mutations to a file in Rosetta's mutfile format with calculated jump indices.

        Args:
            file_path (str): The file path to save the mutation file.
        """
        with open(file_path, "w") as file:
            for mutation in self.mutations:
                rosetta_format = self.protein_sequence.mutation_to_rosetta_format(mutation)
                file.write(f"{rosetta_format}\n")

    @property
    def raw_mutant_id(self) -> str:
        """
        Generates and returns a raw mutant identifier string by concatenating
        chain ID, wild-type residue, position, and mutated residue for each
        mutation in the `mutations` list.
        """
        return "_".join([str(mutation) for mutation in self.mutations])

    @property
    def mutant_score(self) -> float:
        """
        The mutant score property.
        """
        return self._mutant_score

    @mutant_score.setter
    def mutant_score(self, value: float):
        """
        Set the mutant score to a new value.
        """
        self._mutant_score = float(value)

    @classmethod
    def from_pdb(cls, pdb_fp: str, mutant_sequences: dict) -> "Mutant":
        """
        Class method that generates a Mutant object by comparing the wild-type sequence
        extracted from a PDB file with a provided mutant sequence.

        Args:
            pdb_fp (str): Path to the PDB file (wild-type).
            mutant_sequences (dict): Dictionary where keys are chain IDs and values are mutant sequences.

        Returns:
            Mutant: A Mutant object containing the list of mutations and the protein sequence.
        """
        # Parse the PDB file to extract the wild-type sequence
        pdb_parser = PDBParser()
        structure = pdb_parser.get_structure("WT", pdb_fp)

        # Initialize a ProteinSequence object to store the WT sequence
        protein_sequence = ProteinSequence()

        # Extract the WT sequence from the PDB file and add it to the ProteinSequence object
        for model in structure:
            for chain in model:
                chain_id = chain.id
                wt_sequence = ""
                for residue in chain.get_residues():
                    if PDB.is_aa(residue, standard=True):  # Include only standard amino acids
                        wt_sequence += PDB.Polypeptide.three_to_one(residue.get_resname())
                protein_sequence.add_chain(chain_id, wt_sequence)

        # Compare WT sequence with the mutant sequence to find mutations
        mutations = []
        for chain_id, wt_seq in protein_sequence.chains:
            mutant_seq = mutant_sequences.get(chain_id, "")
            for pos, (wt_res, mut_res) in enumerate(zip(wt_seq.sequence, mutant_seq), start=1):
                if wt_res != mut_res:
                    mutation = Mutation(chain_id=chain_id, position=pos, wt_res=wt_res, mut_res=mut_res)
                    mutations.append(mutation)

        # Create and return the Mutant object
        return cls(mutations=mutations, protein_sequence=protein_sequence, _pdb_fp=pdb_fp)
