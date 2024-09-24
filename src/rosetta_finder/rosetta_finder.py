import os
import sys
import re
from pathlib import Path
import re
from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class RosettaBinary:
    dirname: str
    binary_name: str
    mode: Optional[Literal["static", "mpi", "default"]]
    os: Literal["linux", "macos"]
    compiler: Literal["gcc", "clang"]
    release: Literal["release", "debug"]

    @property
    def filename(self) -> str:
        """
        Reconstruct the filename from the binary components.

        Returns:
            str: The reconstructed filename.
        """
        parts = [self.binary_name]
        if self.mode:
            parts.append(f"{self.mode}")
        parts.append(f"{self.os}{self.compiler}{self.release}")
        filename = ".".join(parts)
        return filename

    @property
    def full_path(self) -> str:
        """
        Get the full path to the binary executable.

        Returns:
            str: The full path combining dirname and filename.
        """
        return os.path.join(self.dirname, self.filename)

    @classmethod
    def from_filename(cls, dirname: str, filename: str):
        """
        Create a RosettaBinary instance by parsing the filename.

        Parameters:
            dirname (str): The directory where the binary is located.
            filename (str): The name of the binary file.

        Returns:
            RosettaBinary: An instance of RosettaBinary with parsed attributes.

        Raises:
            ValueError: If the filename does not match the expected pattern.
        """
        # Regular expression to parse the filename
        regex = r"""
            ^(?P<binary_name>.+?)\.
            ((?P<mode>default|mpi|static)\.)?
            (?P<os>linux|macos)
            (?P<compiler>gcc|clang)
            (?P<release>release|debug)$
        """
        pattern = re.compile(regex, re.VERBOSE)
        match = pattern.match(filename)
        if not match:
            raise ValueError(f"Filename '{filename}' does not match the expected pattern.")

        binary_name = match.group("binary_name")
        mode = match.group("mode")
        os_name = match.group("os")
        compiler = match.group("compiler")
        release = match.group("release")

        return cls(dirname=dirname, binary_name=binary_name, mode=mode, os=os_name, compiler=compiler, release=release)


class RosettaFinder:
    def __init__(self, search_path=None):
        """
        Initialize the RosettaFinder with an optional search path.

        Parameters:
            search_path (str or Path): Custom path to search for the binary.
        """
        self.search_path = Path(search_path) if search_path else None

        # OS check: Raise an error if not running on Linux or macOS
        if not sys.platform.startswith(("linux", "darwin")):
            raise EnvironmentError("Unsupported OS. This script only runs on Linux or macOS.")

        # Determine the search paths
        self.search_paths = self.get_search_paths()

    def build_regex_pattern(self, binary_name):
        """
        Build the regex pattern to search for the Rosetta binary.

        Parameters:
            binary_name (str): Name of the Rosetta binary to search for.

        Returns:
            re.Pattern: Compiled regular expression pattern.
        """
        regex_string = rf"{binary_name}\.((default|mpi|static)\.){{0,1}}(linux|macos)(gcc|clang)(release|debug)$"
        return re.compile(regex_string)

    def get_search_paths(self):
        """
        Determine the paths to search for the binary.

        Returns:
            list of Path: List of paths to search.
        """
        paths = []

        # 0. Customized path
        if self.search_path:
            paths.append(self.search_path)

        # 1. ROSETTA_BIN environment variable
        rosetta_bin_env = os.environ.get("ROSETTA_BIN")
        if rosetta_bin_env:
            paths.append(Path(rosetta_bin_env))

        # 2. ROSETTA3/bin
        paths.append(Path("ROSETTA3") / "bin")

        # 3. ROSETTA/main/source/bin/
        paths.append(Path("ROSETTA") / "main" / "source" / "bin")

        return paths

    def find_binary(self, binary_name="rosetta_scripts"):
        """
        Search for the Rosetta binary in the specified paths.

        Parameters:
            binary_name (str): Name of the Rosetta binary to search for.
                               Default is 'rosetta_scripts'.

        Returns:
            Path: Path to the found binary.

        Raises:
            FileNotFoundError: If the binary is not found.
        """
        pattern = self.build_regex_pattern(binary_name)
        for path in self.search_paths:
            if not (path.exists() and path.is_dir()):
                continue
            for file in path.iterdir():
                if not file.is_file():
                    continue
                if not pattern.match(file.name):
                    continue
                try:
                    rosetta_binary = RosettaBinary.from_filename(str(path), file.name)
                    if rosetta_binary.binary_name == binary_name:
                        return rosetta_binary
                except ValueError as e:
                    continue

        raise FileNotFoundError(f"{binary_name} binary not found in the specified paths.")


def main() -> str:
    """
    Main function to find the Rosetta binary.

    Parameters:
        bin_str (str): Name of the Rosetta binary to search for.

    Returns:
        None
    """
    bin_str = sys.argv[1]
    bin_path = sys.argv[2] if len(sys.argv) > 2 else None
    finder = RosettaFinder(bin_path)
    binary_path = finder.find_binary(bin_str)
    if not os.path.isfile(binary_path.full_path):
        raise FileNotFoundError(f"Binary '{binary_path.full_path}' does not exist.")

    print(binary_path.full_path)
    return binary_path.full_path
