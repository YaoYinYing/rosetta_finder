import os
from typing import Optional
from rosetta_finder import Rosetta


def supercharge(
    pdb: str,
    abs_target_charge=20,
    nproc: Optional[int] = 4,
):

    rosetta = Rosetta(
        "supercharge",
        job_id="test_supercharge",
        output_dir="tests/outputs/",
        nproc=nproc,
        opts=[
            "-in:file:s",
            os.path.abspath(pdb),
            "-dont_mutate_glyprocys",
            "true",
            "-dont_mutate_correct_charge",
            "true",
            "-dont_mutate_hbonded_sidechains",
            "true",
            "-include_asp",
            "-include_glu",
            "-refweight_asp",
            "-0.6",
            "-refweight_glu",
            "-0.8",
            "-include_arg",
            "-include_lys",
            "-refweight_arg",
            "-1.98",
            "-refweight_lys",
            "-1.65",
            "-ignore_unrecognized_res",
            "-surface_residue_cutoff",
            "16",
            "-target_net_charge_active",
            "-mute",
            "all",
            "-unmute",
            "protocols.design_opt.Supercharge",
            "-overwrite",
        ],
        save_all_together=True,
    )
    instance = os.path.basename(pdb)[:-4]

    rosetta.run(
        inputs=[
            {"-out:file:scorefile": f"{instance}_charge_{c}.sc", "-target_net_charge": str(c)}
            for c in range(-abs_target_charge, abs_target_charge, 2)
        ]
    )


def main():
    pdb = "tests/data/3fap_hf3_A.pdb"
    supercharge(pdb, nproc=os.cpu_count())


if __name__ == "__main__":
    main()
