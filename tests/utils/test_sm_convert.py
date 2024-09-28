import pytest


from rosetta_finder.app.utils.smiles2param import deprotonate_acids, generate_molecule, get_conformers, protonate_tertiary_amine


# Test case for deprotonate_acids
def test_deprotonate_acids():
    smiles = 'CC(=O)O'  # Acetic acid
    expected = 'CC(=O)[O-]'
    result = deprotonate_acids(smiles)
    assert result == expected, f"Expected {expected}, but got {result}"

def test_protonate_tertiary_amine():
    from rdkit import Chem
    smiles = 'CCN(CC)CC'  # Tertiary amine
    mol = Chem.MolFromSmiles(smiles) # type: ignore
    result_mol = protonate_tertiary_amine(mol)
    nitrogen_idx = [atom.GetIdx() for atom in result_mol.GetAtoms() if atom.GetAtomicNum() == 7][0] # type: ignore
    charge = result_mol.GetAtomWithIdx(nitrogen_idx).GetFormalCharge()  # type: ignore # Check nitrogen atom charge
    assert charge == 1, f"Expected charge of 1, but got {charge}"


# Test case for generate_molecule
def test_generate_molecule():
    name = 'test_molecule'
    smiles = 'CCO'  # Ethanol
    mol = generate_molecule(name, smiles)
    expected_num_atoms = 9  # 3 atoms (C, C, O) + 6 H atoms
    assert mol.GetNumAtoms() == expected_num_atoms, f"Expected {expected_num_atoms} atoms, but got {mol.GetNumAtoms()}"
    assert mol.GetProp("_Name") == name, f"Expected name {name}, but got {mol.GetProp('_Name')}"


# Test case for get_conformers
def test_get_conformers():
    smiles = 'CCO'  # Ethanol
    mol = generate_molecule('ethanol', smiles)
    num_conformers = 5
    conf_ids = get_conformers(mol, nr=num_conformers, rmsthreshold=0.001)  # Lower the threshold to avoid pruning
    assert len(conf_ids) == num_conformers, f"Expected {num_conformers} conformers, but got {len(conf_ids)}"
