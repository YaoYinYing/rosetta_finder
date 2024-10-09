import copy
from dataclasses import dataclass, field

from typing import Dict, List, Optional, Union
import subprocess
import os

import warnings
from datetime import datetime


# internal imports
from .rosetta_finder import RosettaBinary, RosettaFinder
from .utils import isolate
from .node import MPI_node
from .node.mpi import MPI_IncompatibleInputWarning


class RosettaScriptVariableWarning(RuntimeWarning): ...


class RosettaScriptVariableNotExistWarning(RosettaScriptVariableWarning): ...


class IgnoreMissingFileWarning(UserWarning): ...


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
        for k, v in self.asdict.items():
            if f"%%{k}%%" not in xml_content_copy:
                warnings.warn(RosettaScriptVariableNotExistWarning(f"Variable {k} not in Rosetta Script content."))
                continue
            xml_content_copy = xml_content_copy.replace(f"%%{k}%%", v)

        return xml_content_copy


@dataclass
class RosettaCmdTask:
    cmd: List[str]
    task_label: Optional[str] = None
    base_dir: Optional[str] = "tests/outputs/runtimes/"  # a base directory for run local task

    @property
    def runtime_dir(self) -> str:  # The directory for storing runtime output
        if not self.task_label:
            raise ValueError("task_label is required for calling this attribute")

        if not self.base_dir:
            warnings.warn("Fixing base_dir to `runtime`")
            self.base_dir = os.path.abspath("runtime")

        return os.path.join(self.base_dir, self.task_label)


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

    isolation: bool = False

    @staticmethod
    def expand_input_dict(d: Dict[str, Union[str, RosettaScriptsVariableGroup]]) -> List[str]:
        """
        Expands a dictionary containing strings and variable groups into a flat list.

        :param d: Dictionary with keys and values that can be either strings or variable groups.
        :return: A list of expanded key-value pairs.
        """

        opt_list = []
        for k, v in d.items():
            if not isinstance(v, RosettaScriptsVariableGroup):
                opt_list.extend([k, v])
            else:
                opt_list.extend(v.aslonglist)
        return opt_list

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
                warnings.warn(
                    UserWarning("MPI nodes are given yet not supported. Maybe in Dockerized Rosetta container?")
                )

            self.use_mpi = True
            return

        else:
            warnings.warn(UserWarning("Using MPI binary as static build."))
            self.use_mpi = False

    @staticmethod
    def _isolated_execute(task: RosettaCmdTask) -> RosettaCmdTask:
        if not task.task_label:
            raise ValueError("Task label is required when executing the command in isolated mode.")

        if not task.base_dir:
            raise ValueError("Base directory is required when executing the command in isolated mode.")

        with isolate(save_to=task.runtime_dir):
            return Rosetta._non_isolated_execute(task)

    @staticmethod
    def execute(task: RosettaCmdTask) -> RosettaCmdTask:
        if not task.task_label:
            return Rosetta._non_isolated_execute(task)
        return Rosetta._isolated_execute(task)

    @staticmethod
    def _non_isolated_execute(task: RosettaCmdTask) -> RosettaCmdTask:
        """
        Executes a command and handles its output and errors.

        :param cmd: Command to be executed.
        """
        process = subprocess.Popen(
            task.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf-8"
        )

        print(f'Lauching command: {" ".join(task.cmd)}')
        stdout, stderr = process.communicate()
        retcode = process.wait()

        if retcode:
            print(f"Command failed with return code {retcode}")
            print(stdout)
            warnings.warn(RuntimeWarning(stderr))
            raise RuntimeError(f"Command failed with return code {retcode}")

        return task

    def run_mpi(
        self,
        base_cmd: List[str],
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[RosettaCmdTask]:
        """
        Runs a command using MPI.

        :param cmd: Base command to be executed.
        :param inputs: List of input dictionaries.
        :param nstruct: Number of structures to generate.
        :return: List of Nones for counting.
        """
        assert isinstance(self.mpi_node, MPI_node), "MPI node instance is not initialized."

        _base_cmd = copy.copy(base_cmd)
        if inputs:
            for i, _i in enumerate(inputs):
                _base_cmd.extend(self.expand_input_dict(_i))

        if nstruct:
            ret = _base_cmd.extend(["-nstruct", str(nstruct)])

        with self.mpi_node.apply(_base_cmd) as updated_cmd:
            if self.isolation:
                warnings.warn(RuntimeWarning("Ignoring isolated mode for MPI run."))
            ret = Rosetta._non_isolated_execute(RosettaCmdTask(cmd=updated_cmd))

        return [ret]

    def run_local(
        self,
        base_cmd: List[str],
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[RosettaCmdTask]:
        """
        Runs a command locally, possibly in parallel.

        :param cmd: Base command to be executed.
        :param inputs: List of input dictionaries.
        :param nstruct: Number of structures to generate.
        :return: List of Nones for counting.
        """
        from joblib import Parallel, delayed

        _base_cmd = copy.copy(base_cmd)

        now = datetime.now().strftime("%Y%m%d_%H%M%S")  # formatted date-time

        if nstruct and nstruct > 0:

            if inputs:
                for i, _i in enumerate(inputs):
                    __i = self.expand_input_dict(_i)
                    _base_cmd.extend(__i)
                    print(f"Additional input args is passed: {__i}")

            cmd_jobs = [
                RosettaCmdTask(
                    cmd=_base_cmd
                    + [
                        "-suffix",
                        f"_{i:05}",
                        "-no_nstruct_label",
                        "-out:file:scorefile",
                        f"{self.job_id}.score.{i:05}.sc",
                    ],
                    task_label=f"task_{self.job_id}-{i:05}" if self.isolation else None,
                    base_dir=os.path.join(self.output_dir, f"{now}-{self.job_id}-runtimes"),
                )
                for i in range(1, nstruct + 1)
            ]
            warnings.warn(UserWarning(f"Processing {len(cmd_jobs)} commands on {nstruct} decoys."))
        elif inputs:
            cmd_jobs = [
                RosettaCmdTask(
                    cmd=_base_cmd + self.expand_input_dict(input_arg),
                    task_label=f"task-{self.job_id}-no-{i}" if self.isolation else None,
                    base_dir=os.path.join(self.output_dir, f"{now}-{self.job_id}-runtimes"),
                )
                for i, input_arg in enumerate(inputs)
            ]
            warnings.warn(UserWarning(f"Processing {len(cmd_jobs)} commands"))
        else:
            cmd_jobs = [_base_cmd]

            warnings.warn(UserWarning("No inputs are given. Running single job."))

        ret = Parallel(n_jobs=self.nproc, verbose=100)(delayed(Rosetta.execute)(cmd_job) for cmd_job in cmd_jobs)
        # warnings.warn(UserWarning(str(ret)))
        return list(ret)  # type: ignore

    def run(
        self,
        inputs: Optional[List[Dict[str, Union[str, RosettaScriptsVariableGroup]]]] = None,
        nstruct: Optional[int] = None,
    ) -> List[RosettaCmdTask]:
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
                    warnings.warn(IgnoreMissingFileWarning(f"Ignore Flag - {flag}"))
                    continue
                cmd.append(f"@{os.path.abspath(flag)}")

        if self.opts:
            cmd.extend([opt for opt in self.opts if isinstance(opt, str)])

            any_rosettascript_vars = [opt for opt in self.opts if isinstance(opt, RosettaScriptsVariableGroup)]
            if any(any_rosettascript_vars):
                for v in any_rosettascript_vars:
                    _v = v.aslonglist
                    print(f"Composing command with {_v}")
                    cmd.extend(_v)

        if self.output_dir:
            cmd.extend(
                [
                    "-out:path:pdb",
                    os.path.abspath(self.output_pdb_dir),
                    "-out:path:score",
                    os.path.abspath(self.output_scorefile_dir),
                ]
            )

        return cmd
