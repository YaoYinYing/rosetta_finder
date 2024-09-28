import os
from abc import ABC


class RosettaApplication(ABC):

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id

    def prepare(self):
        if hasattr(self, "pdb") and isinstance(self.pdb, str) and os.path.isfile(self.pdb):  # type:ignore
            self.instance = os.path.basename(self.pdb)[:-4]  # type:ignore
            self.pdb = os.path.abspath(self.pdb)  # type:ignore

        if hasattr(self, "save_dir"):
            os.makedirs(os.path.join(self.save_dir, self.job_id), exist_ok=True)  # type:ignore
            self.save_dir = os.path.abspath(self.save_dir)  # type:ignore


from .supercharge import supercharge
from .pross import PROSS
from .rosettaligand import RosettaLigand


__all__ = ["RosettaApplication", "supercharge", "PROSS", "RosettaLigand"]
