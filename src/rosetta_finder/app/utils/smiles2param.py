#!/usr/bin/env python
# coding: utf-8

# # Design of small molecule binders
#

# Data were obtained from pubchem
#
# (https://pubchem.ncbi.nlm.nih.gov/compound/3345#section=Top)

# The python script for the generating the parameter file has to be set:
# python2.7 /Users/pgreisen/Programs/Rosetta/Rosetta/main/source/scripts/python/public/molfile_to_params.py
#



from dataclasses import dataclass
import os
import sys
from typing import Dict, Optional
import pandas as pd

import subprocess
from rdkit import Chem
from rdkit import DataStructs
from rdkit.Chem import AllChem
from rdkit.Chem.Fingerprints import FingerprintMols
from rosetta_finder import RosettaBinary


# Functions
def deprotonate_acids(smiles):
    deprotonate_cooh = AllChem.ReactionFromSmarts("[C:1](=[O:2])-[OH1:3]>>[C:1](=[O:2])-[O-H0:3]") # type: ignore
    mol = Chem.MolFromSmiles(smiles) # type: ignore
    m_deprot = deprotonate_cooh.RunReactants((mol,))
    if (len(m_deprot) != 0):
        smiles = Chem.MolToSmiles(m_deprot[0][0]) # type: ignore
    return smiles


def protonate_tertiary_amine(mol):
    patt_1 = Chem.MolFromSmarts('[^3]') # type: ignore
    print(patt_1)
    matches_1 = mol.GetSubstructMatches(patt_1)
    patt_2 = Chem.MolFromSmarts('[#7]') # type: ignore
    matches_2 = mol.GetSubstructMatches(patt_2)
    if (len(matches_1) > 0 and len(matches_2) > 0):
        a = set(matches_1)
        b = set(matches_2)
        ntert = a.intersection(b)
        for n in ntert:
            molStrings = Chem.MolToSmiles(mol, isomericSmiles=True) # type: ignore
            atomSymbol9 = mol.GetAtomWithIdx(n[0]).GetSymbol()
            formalCharge9 = mol.GetAtomWithIdx(n[0]).GetFormalCharge()
            test7 = Chem.AllChem.CalcMolFormula(mol) # type: ignore
            mol.GetAtomWithIdx(n[0]).SetFormalCharge(1)
            # update property cache and check for nonsense
            mol.UpdatePropertyCache()
            return mol
    else:

        return mol



def generate_molecule(name, smiles):
    """
    Generate the 3D molecular structure based on input SMILES
    ----------
    name : name of molecule
    smiles: SMILES of molecule
    Returns
    ----------
    Mol

    """
    LIGAND_NAME = name
    m = Chem.MolFromSmiles(smiles) # type: ignore
    # print(m)
    # m = protonate_tertiary_amine(m)
    # print(m)
    m_h = Chem.AddHs(m) # type: ignore
    # Embeed the geometry
    AllChem.EmbedMolecule(m_h, AllChem.ETKDG()) # type: ignore
    # Setting name of molecule
    m_h.SetProp("_Name", LIGAND_NAME)
    return m_h


def get_conformers(mol, nr=500, rmsthreshold=0.1):
    """
    Generate 3D conformers of molecule using CSD-method
    ----------
    mol : RKdit molecule
    nr : integer, number of conformers to be generate
    rmsthreshold : float, prune conformers that are less rms away from another conf
    Returns
    ----------
    List of new conformation IDs
    """
    # Generate conformers on the CSD-method
    return AllChem.EmbedMultipleConfs(mol, numConfs=nr, useBasicKnowledge=True, pruneRmsThresh=rmsthreshold, # type: ignore
                                      useExpTorsionAnglePrefs=True)





#
# def select_molecule(molecule):
# 	new_i = widgets.interactive(print_city, country=countryW, city=geoWs[country['new']])
# 	i.children = new_i.children
#
#
# def on_change(change):
# 	from IPython.display import clear_output
# 	clear_output()
# 	molconf_widget.value = 'Number of conformers: ' + str(mols[change['new']].GetNumConformers())
# 	display(container)
# 	interact(drawit, m=fixed(mols[change['new']]), p=fixed(p), confId=(0, mols[change['new']].GetNumConformers() - 1));

@dataclass
class SmallMoleculeParamsGenerator:
    rosetta_bin:Optional[RosettaBinary]=None

    num_conformer: int = 100
    save_dir: str = './ligands/'

    # internal
    rosetta_python_script_dir: str=''


    def __post_init__(self):
        if isinstance(self.rosetta_bin, RosettaBinary):
            p=os.path.join(self.rosetta_bin.dirname, '../','scripts/python/public')
            if os.path.exists(p):
                self.rosetta_python_script_dir=p
                return

        if os.environ.get('ROSETTA_PYTHON_SCRIPTS') is not None:
            self.rosetta_python_script_dir=os.environ['ROSETTA_PYTHON_SCRIPTS']
            return

        if os.environ.get('ROSETTA') is not None:
            self.rosetta_python_script_dir=os.path.join(os.environ['ROSETTA'], 'main/source/scripts/python/public/')
            return
        if os.environ.get('ROSETTA3') is not None:
            self.rosetta_python_script_dir=os.path.join(os.environ['ROSETTA3'], 'scripts/python/public/')
            return

        raise RuntimeError('Could not find a proper directory like ROSETTA_PYTHON_SCRIPTS, ROSETTA, or ROSETTA3. Maybe in Dockerized?')



    def convert(self, ligands: Dict[str, str]):
        c_smiles = []
        for i,ds in ligands.items():

            try:
                cs = Chem.CanonSmiles(ds)
                c_smiles.append(cs)
            except:
                print('Invalid SMILES: %s\n%s' % (i, ds))
        print(c_smiles)

        # make a list of mols
        ms = [Chem.MolFromSmiles(x) for x in c_smiles] # type: ignore

        # make a list of fingerprints (fp)
        fps = [FingerprintMols.FingerprintMol(x) for x in ms]

        # the list for the dataframe
        qu, ta, sim = [], [], []

        # compare all fp pairwise without duplicates
        for n in range(len(fps) - 1):  # -1 so the last fp will not be used
            s = DataStructs.BulkTanimotoSimilarity(fps[n], fps[n + 1:])  # type: ignore # +1 compare with the next to the last fp
            print(c_smiles[n], c_smiles[n + 1:])  # witch mol is compared with what group
            # collect the SMILES and values
            for m in range(len(s)):
                qu.append(c_smiles[n])
                ta.append(c_smiles[n + 1:][m])
                sim.append(s[m])
        print()

        # build the dataframe and sort it
        d = {'query': qu, 'target': ta, 'Similarity': sim}
        df_final = pd.DataFrame(data=d)
        df_final = df_final.sort_values('Similarity', ascending=False)
        print(df_final)

        mols = {}
        updated_ligands = {}
        for name,ds in ligands.items():
            updated_ligands[name] = deprotonate_acids(ds)
            mols[name] = generate_molecule(name, ds)

        # processing ligands
        for i in ligands:
            cids = get_conformers(mols[i], self.num_conformer, 0.1)
            # Do a short minimization and compute the RMSD
            for cid in cids:
                _ = AllChem.MMFFOptimizeMolecule(mols[i], confId=cid) # type: ignore
            rmslist = []
            AllChem.AlignMolConformers(mols[i], RMSlist=rmslist) # type: ignore


        for key in mols:
            self.generate_rosetta_input(mol=mols[key], name=key, charge=Chem.GetFormalCharge(mols[key])) # type: ignore



    def generate_rosetta_input(self, mol, name, charge=0):
        os.makedirs(f"{self.save_dir}/{name}", exist_ok=True)
        wd = os.getcwd()
        os.chdir(f"{self.save_dir}/{name}")
        w = Chem.SDWriter(f'{name}.sdf') # type: ignore
        for i in mol.GetConformers():
            w.write(mol, confId=i.GetId())
        w.close()

        exe = [sys.executable, os.path.join(self.rosetta_python_script_dir,'molfile_to_params.py'), f'{name}.sdf', '-n', name, '--conformers-in-one-file', f'--recharge={str(charge)}', '-c']
        print(f'Launching script: {" ".join(exe)}')
        subprocess.Popen(exe)
        print(exe)
        os.chdir(wd)