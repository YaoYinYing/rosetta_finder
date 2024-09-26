import os
from typing import Optional
from dataclasses import dataclass
from rosetta_finder import Rosetta, RosettaScriptsVariableGroup, RosettaEnergyUnitAnalyser
from rosetta_finder.utils import timing
from rosetta_finder.app.utils import PDBProcessor

script_dir = os.path.dirname(os.path.abspath(__file__))


@dataclass
class PROSS:
    pdb: str
    pssm: str

    res_to_fix: str = "1A"
    blast_bin: Optional[str] = None
    uniref90_db_blast: Optional[str] = None

    save_dir: str = "tests/outputs"
    job_id: str = "pross"

    CA_constraints: str = ""
    instance: str = ""

    def __post_init__(self):
        self.instance = os.path.basename(self.pdb)[:-4]
        os.makedirs(os.path.join(self.save_dir, self.job_id), exist_ok=True)

        self.CA_constraints = os.path.join(self.save_dir, self.job_id, f"{self.instance}_bbCA.cst")
        PDBProcessor.convert_pdb_to_constraints(self.pdb, self.CA_constraints)

    def refine(self, nstruct=1):
        refinement_dir = os.path.join(self.save_dir, self.job_id, "refinement")

        rosetta = Rosetta(
            bin="rosetta_scripts",
            flags=[os.path.join(script_dir, "deps/pross/flag/flags_nodelay")],
            opts=[
                "-parser:protocol",
                f"{script_dir}/deps/pross/xml/refine.xml",
                RosettaScriptsVariableGroup.from_dict(
                    {
                        "cst_value": "0.4",
                        "cst_full_path": self.CA_constraints,
                        "pdb_reference": self.pdb,
                        "res_to_fix": self.res_to_fix,
                    }
                ),
            ],
            output_dir=refinement_dir,
            save_all_together=False,
            job_id="pross_refinement",
        )

        with timing("PROSS: Refinement"):
            rosetta.run(inputs=[{"-in:file:s": self.pdb}], nstruct=nstruct)

        best_refined_decoy = RosettaEnergyUnitAnalyser(rosetta.output_scorefile_dir)


def main():
    pross = PROSS(pdb="tests/data/3fap_hf3_A.pdb", pssm="tests/data/3fap_hf3_A_ascii_mtx_file")
    pross.refine(30)


if __name__ == "__main__":
    main()
