from dataclasses import dataclass
import os

import warnings

from rosetta_finder.rosetta import IgnoreMissingFileWarning


@dataclass
class RosettaApplication:

    job_id: str

    def prepare(self):
        if hasattr(self, "pdb") and isinstance(self.pdb, str):
            if not os.path.isfile(self.pdb):  # type:ignore
                warnings.warn(IgnoreMissingFileWarning(f"PDB is given yet not found - {self.pdb}"))
            self.instance = os.path.basename(self.pdb)[:-4]  # type:ignore
            self.pdb = os.path.abspath(self.pdb)  # type:ignore

        if hasattr(self, "save_dir"):
            os.makedirs(os.path.join(self.save_dir, self.job_id), exist_ok=True)  # type:ignore
            self.save_dir = os.path.abspath(self.save_dir)  # type:ignore


from .supercharge import supercharge
from .pross import PROSS
from .rosettaligand import RosettaLigand


__all__ = ["RosettaApplication", "supercharge", "PROSS", "RosettaLigand"]
