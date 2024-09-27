import copy
from dataclasses import dataclass, field
import shutil
import sys
import time
from typing import Dict, List, Literal, Optional, Tuple, Union
import subprocess
import os
import random
import contextlib
import warnings
import platform

import pandas as pd

# internal imports
from .rosetta_finder import RosettaBinary, RosettaFinder


class MPI_IncompatibleInputWarning(RuntimeWarning): ...


class RosettaScriptVariableWarning(RuntimeWarning): ...


class RosettaScriptVariableNotExistWarning(RosettaScriptVariableWarning): ...


@dataclass(frozen=True)
class RosettaScriptsVariable:
    k: str
    v: str

    @property
    def aslist(self) -> List[str]:
        return [
            "-parser:script_vars",
            f"{self.k}={self.v}",
        ]


@dataclass(frozen=True)
class RosettaScriptsVariableGroup:
    variables: List[RosettaScriptsVariable]

    @property
    def empty(self):
        return len(self.variables) == 0

    @property
    def aslonglist(self) -> List[str]:
        return [i for v in self.variables for i in v.aslist]

    @property
    def asdict(self) -> Dict[str, str]:
        return {rsv.k: rsv.v for rsv in self.variables}

    @classmethod
    def from_dict(cls, var_pair: Dict[str, str]) -> "RosettaScriptsVariableGroup":
        variables = [RosettaScriptsVariable(k=k, v=str(v)) for k, v in var_pair.items()]
        instance = cls(variables)
        if instance.empty:
            raise ValueError()
        return instance

    def apply_to_xml_content(self, xml_content: str):
        xml_content_copy = copy.deepcopy(xml_content)
        for k, v in self.asdict:
            if f"%%{k}%%" not in xml_content_copy:
                warnings.warn(RosettaScriptVariableNotExistWarning(f"Variable {k} not in Rosetta Script content."))
                continue
            xml_content_copy = xml_content_copy.replace(f"%%{k}%%", v)

        return xml_content_copy


@dataclass
class MPI_node:
    nproc: int = 0
    node_matrix: Optional[Dict[str, int]] = None  # Node ID: nproc
    node_file = f"nodefile_{random.randint(1,9_999_999_999)}.txt"

    user=os.getuid()

    def __post_init__(self):

        for mpi_exec in ["mpirun", "mpicc", ...]:
            self.mpi_excutable = shutil.which(mpi_exec)
            if self.mpi_excutable is not None:
                break

        if not isinstance(self.node_matrix, dict):
            return

        with open(self.node_file, "w") as f:
            for node, nproc in self.node_matrix.items():
                f.write(f"{node} slots={nproc}\n")
        self.nproc = sum(self.node_matrix.values())  # fix nproc to real node matrix

    @property
    def local(self) -> List[str]:
        return [self.mpi_excutable, "--use-hwthread-cpus", "-np", str(self.nproc)]

    @property
    def host_file(self) -> List[str]:
        return [self.mpi_excutable, "--hostfile", self.node_file]

    @contextlib.contextmanager
    def apply(self, cmd: List[str]):
        cmd_copy = copy.copy(cmd)
        m = self.local if not self.node_matrix else self.host_file
        if self.user == 0:
            m.append('--allow-run-as-root')
            warnings.warn(UserWarning('Running Rosetta with MPI as Root User'))

        yield m + cmd_copy

        if os.path.isfile(self.node_file):
            os.remove(self.node_file)

    @classmethod
    def from_slurm(cls) -> "MPI_node":
        try:
            nodes = (
                subprocess.check_output(["scontrol", "show", "hostnames", os.environ["SLURM_JOB_NODELIST"]])
                .decode()
                .strip()
                .split("\n")
            )
        except KeyError as e:
            raise RuntimeError(f"Environment variable {e} not set") from None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get node list: {e.output}") from None

        slurm_cpus_per_task = os.environ.get("SLURM_CPUS_PER_TASK", "1")
        slurm_ntasks_per_node = os.environ.get("SLURM_NTASKS_PER_NODE", "1")

        if int(slurm_cpus_per_task) < 1:
            print(f"Fixing $SLURM_CPUS_PER_TASK from {slurm_cpus_per_task} to 1.")
            slurm_cpus_per_task = "1"

        if int(slurm_ntasks_per_node) < 1:
            print(f"Fixing $SLURM_NTASKS_PER_NODE from {slurm_ntasks_per_node} to 1.")
            slurm_ntasks_per_node = "1"

        node_dict = {i: int(slurm_ntasks_per_node) * int(slurm_cpus_per_task) for i in nodes}

        total_nproc = sum(node_dict.values())
        return cls(total_nproc, node_dict)


@dataclass
class Rosetta:
    """
    A wrapper class for running Rosetta command-line applications.

    Attributes:
        bin (RosettaBinary): The Rosetta binary to execute.
        nproc (int): Number of processors to use.
        flags (List[str]): List of flag files to include.
        opts (List[str]): List of command-line options.
        use_mpi (bool): Whether to use MPI for execution.
        mpi_node (MPI_node): MPI node configuration.
    """

    bin: Union[RosettaBinary, str]
    nproc: Union[int, None] = field(default_factory=os.cpu_count)

    flags: Optional[List[str]] = field(default_factory=list)
    opts: Optional[List[Union[str, RosettaScriptsVariableGroup]]] = field(default_factory=list)
    use_mpi: bool = False
    mpi_node: Optional[MPI_node] = None

    job_id: str = "default"
    output_dir: str = ""
    save_all_together: bool = False

    @staticmethod
    def expand_input_dict(d: Dict[str, Union[str, RosettaScriptsVariableGroup]]) -> List[str]:
        """
        Expands a dictionary containing strings and variable groups into a flat list.

        :param d: Dictionary with keys and values that can be either strings or variable groups.
        :return: A list of expanded key-value pairs.
        """

        l = []
        for k, v in d.items():
            if not isinstance(v, RosettaScriptsVariableGroup):
                l.extend([k, v])
            else:
                l.extend(v.aslonglist)
        return l

    @property
    def output_pdb_dir(self) -> str:
        """
        Returns the path to the PDB output directory, creating it if necessary.

        :return: Path to the PDB output directory.
        """
        if not self.output_dir:
            raise ValueError("Output directory not set.")
        p = os.path.join(self.output_dir, self.job_id, "pdb" if not self.save_all_together else "all")
        os.makedirs(p, exist_ok=True)
        return p

    @property
    def output_scorefile_dir(self) -> str:
        """
        Returns the path to the score file output directory, creating it if necessary.

        :return: Path to the score file output directory.
        """
        if not self.output_dir:
            raise ValueError("Output directory not set.")
        p = os.path.join(self.output_dir, self.job_id, "scorefile" if not self.save_all_together else "all")
        os.makedirs(p, exist_ok=True)
        return p

    def __post_init__(self):
        """
        Post-initialization setup for the Rosetta job configuration.
        """
        if self.flags is None:
            self.flags = []
        if self.opts is None:
            self.opts = []

        if isinstance(self.bin, str):
            self.bin = RosettaFinder().find_binary(self.bin)

        if self.mpi_node is not None:
            if self.bin.mode != "mpi":
                warnings.warn(UserWarning("MPI nodes are given yet not supported. Maybe in Dockerized Rosetta container?"))

            self.use_mpi = True
            return

        else:
            warnings.warn(UserWarning("Using MPI binary as static build."))
            self.use_mpi = False

    @staticmethod
    def execute(cmd: List[str]) -> None:
        """
        Executes a command and handles its output and errors.

        :param cmd: Command to be executed.
        """
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
        )

        print(f'Lauching command: {" ".join(cmd)}')
        stdout, stderr = process.communicate()
        retcode = process.wait()

        if retcode:
            print(f"Command failed with return code {retcode}")
            print(stdout)
            print(stderr)
            raise RuntimeError(f"Command failed with return code {retcode}")

    def run_mpi(
        self,
        cmd: List[str],
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[None]:
        """
        Runs a command using MPI.

        :param cmd: Base command to be executed.
        :param inputs: List of input dictionaries.
        :param nstruct: Number of structures to generate.
        :return: List of Nones for counting.
        """
        assert isinstance(self.mpi_node, MPI_node), "MPI node instance is not initialized."

        _cmd = copy.copy(cmd)
        if inputs:
            for i, _i in enumerate(inputs):
                _cmd.extend(self.expand_input_dict(_i))

        if nstruct:
            ret = _cmd.extend(["-nstruct", str(nstruct)])
        with self.mpi_node.apply(_cmd) as updated_cmd:
            ret = self.execute(updated_cmd)

        return [ret]

    def run_local(
        self,
        cmd: List[str],
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[None]:
        """
        Runs a command locally, possibly in parallel.

        :param cmd: Base command to be executed.
        :param inputs: List of input dictionaries.
        :param nstruct: Number of structures to generate.
        :return: List of Nones for counting.
        """
        from joblib import Parallel, delayed

        _cmd = copy.copy(cmd)

        if nstruct and nstruct > 0:

            if inputs:
                for i, _i in enumerate(inputs):
                    __i = self.expand_input_dict(_i)
                    _cmd.extend(__i)
                    print(f"Additional input args is passed: {__i}")

            cmd_jobs = [
                _cmd
                + ["-suffix", f"_{i:05}", "-no_nstruct_label", "-out:file:scorefile", f"{self.job_id}.score.{i:05}.sc"]
                for i in range(1, nstruct + 1)
            ]
            warnings.warn(UserWarning(f"Processing {len(cmd_jobs)} commands on {nstruct} decoys."))
        elif inputs:
            cmd_jobs = [_cmd + self.expand_input_dict(input_arg) for input_arg in inputs]
            warnings.warn(UserWarning(f"Processing {len(cmd_jobs)} commands"))
        else:
            cmd_jobs = [_cmd]

            warnings.warn(UserWarning("No inputs are given. Running single job."))

        ret = Parallel(n_jobs=self.nproc, verbose=100)(
            delayed(self.execute)(cmd_job) for cmd_job in cmd_jobs
        )  # type: ignore
        # warnings.warn(UserWarning(str(ret)))
        return list(ret)

    def run(
        self,
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[None]:
        """
        Runs the command either using MPI or locally based on configuration.

        :param inputs: List of input dictionaries.
        :param nstruct: Number of structures to generate.
        :return: List of Nones.
        """
        cmd = self.compose(opts=self.opts)
        if self.use_mpi and isinstance(self.mpi_node, MPI_node):
            if inputs is not None:
                warnings.warn(
                    MPI_IncompatibleInputWarning(
                        "Customized Inputs for MPI nodes will be flattened and passed to master node"
                    )
                )
            return self.run_mpi(cmd, inputs=inputs, nstruct=nstruct)

        return self.run_local(cmd, inputs, nstruct)

    def compose(self, **kwargs) -> List[str]:
        """
        Composes the full command based on the provided options.

        :return: The composed command as a list of strings.
        """
        assert isinstance(self.bin, RosettaBinary), "Rosetta binary must be a RosettaBinary object"

        cmd = [
            self.bin.full_path,
        ]
        if self.flags:
            for flag in self.flags:
                if not os.path.isfile(flag):
                    continue
                cmd.append(f"@{flag}")

        if self.opts:
            cmd.extend([opt for opt in self.opts if isinstance(opt, str)])

            any_rosettascript_vars = [opt for opt in self.opts if isinstance(opt, RosettaScriptsVariableGroup)]
            if any(any_rosettascript_vars):
                for v in any_rosettascript_vars:
                    _v = v.aslonglist
                    print(f"Composing command with {_v}")
                    cmd.extend(_v)

        if self.output_dir:
            cmd.extend(["-out:path:pdb", self.output_pdb_dir, "-out:path:score", self.output_scorefile_dir])

        return cmd


@dataclass
class RosettaEnergyUnitAnalyser:
    """
    A tool class for analyzing Rosetta energy calculation results.

    Parameters:
    - score_file (str): The path to the score file or directory containing score files.
    - score_term (str, optional): The column name in the score file to use as the score. Defaults to "total_score".
    - job_id (Optional[str], optional): An identifier for the job. Defaults to None.
    """

    score_file: str
    score_term: str = "total_score"

    job_id: Optional[str] = None

    @staticmethod
    def scorefile2df(score_file: str) -> pd.DataFrame:
        """
        Converts a score file into a pandas DataFrame.

        Parameters:
        - score_file (str): Path to the score file.

        Returns:
        - pd.DataFrame: DataFrame containing the data from the score file.
        """
        df = pd.read_fwf(score_file, skiprows=1)

        if "SCORE:" in df.columns:
            df.drop("SCORE:", axis=1, inplace=True)

        return df

    def __post_init__(self):
        """
        Initializes the DataFrame based on the provided score file or directory.
        """
        if os.path.isfile(self.score_file):
            self.df = self.scorefile2df(self.score_file)
        elif os.path.isdir(self.score_file):
            dfs = [
                self.scorefile2df(os.path.join(self.score_file, f))
                for f in os.listdir(self.score_file)
                if f.endswith(".sc")
            ]
            warnings.warn(UserWarning(f"Concatenate {len(dfs)} score files"))
            self.df = pd.concat(dfs, axis=0, ignore_index=True)
        else:
            raise FileNotFoundError(f"Score file {self.score_file} not found.")

        if not self.score_term in self.df.columns:
            raise ValueError(f'Score term "{self.score_term}" not found in score file.')

    @staticmethod
    def df2dict(dfs: pd.DataFrame, k: str = "total_score") -> Tuple[Dict[Literal["score", "decoy"], Union[str, float]]]:
        """
        Converts a DataFrame into a tuple of dictionaries with scores and decoys.

        Parameters:
        - dfs (pd.DataFrame): DataFrame containing the scores.
        - k (str, optional): Column name to use as the score. Defaults to "total_score".

        Returns:
        - Tuple[Dict[Literal["score", "decoy"], Union[str, float]]]: Tuple of dictionaries containing scores and decoys.
        """
        t = tuple(
            {
                "score": float(dfs[dfs.index == i][k].iloc[0]),
                "decoy": str(dfs[dfs.index == i]["description"].iloc[0]),
            }
            for i in dfs.index
        )

        return t  # type: ignore

    @property
    def best_decoy(self) -> Dict[Literal["score", "decoy"], Union[str, float]]:
        """
        Returns the best decoy based on the score term.

        Returns:
        - Dict[Literal["score", "decoy"], Union[str, float]]: Dictionary containing the score and decoy of the best entry.
        """
        if self.df.empty:
            return {}
        return self.top(1)[0]

    def top(
        self, rank: int = 1, score_term: Optional[str] = None
    ) -> Tuple[Dict[Literal["score", "decoy"], Union[str, float]]]:
        """
        Returns the top `rank` decoys based on the specified score term.

        Parameters:
        - rank (int, optional): The number of top entries to return. Defaults to 1.
        - score_term (Optional[str], optional): The column name to use as the score. Defaults to the class attribute `score_term`.

        Returns:
        - Tuple[Dict[Literal["score", "decoy"], Union[str, float]]]: Tuple of dictionaries containing scores and decoys of the top entries.
        """
        if rank <= 0:
            raise ValueError(f"Rank must be greater than 0")

        # Override score_term if provided
        score_term = score_term if score_term is not None and score_term in self.df.columns else self.score_term

        df = self.df.sort_values(
            by=score_term if score_term is not None and score_term in self.df.columns else self.score_term
        ).head(rank)

        return self.df2dict(dfs=df, k=score_term)
