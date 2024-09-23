# RosettaFinder

A Python utility for finding Rosetta binaries based on a specific naming convention.

## Overview

`RosettaFinder` is a Python module designed to locate Rosetta biomolecular modeling suite binaries that follow a specific naming pattern. It searches predefined directories and can handle custom search paths. The module includes:

- An object-oriented `RosettaFinder` class to search for binaries.
- A `RosettaBinary` dataclass to represent the binary and its attributes.
- Unit tests to ensure reliability and correctness.

## Features

- **Flexible Binary Search**: Finds Rosetta binaries based on their naming convention.
- **Platform Support**: Supports Linux and macOS operating systems.
- **Customizable Search Paths**: Allows specification of custom directories to search.
- **Structured Binary Representation**: Uses a dataclass to encapsulate binary attributes.
- **Unit Tested**: Includes tests for both classes to ensure functionality.

## Naming Convention

The binaries are expected to follow this naming pattern:

```
rosetta_scripts[.mode].oscompilerrelease
```

- **Binary Name**: `rosetta_scripts` (default) or specified.
- **Mode** (optional): `default`, `mpi`, or `static`.
- **OS**: `linux` or `macos`.
- **Compiler**: `gcc` or `clang`.
- **Release**: `release` or `debug`.

Examples of valid binary filenames:

- `rosetta_scripts.linuxgccrelease`
- `rosetta_scripts.mpi.macosclangdebug`
- `rosetta_scripts.static.linuxgccrelease`

## Installation

Ensure you have Python 3.6 or higher installed.

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/rosetta_finder.git
   cd rosetta_finder
   ```

2. **Install Dependencies**

   No external dependencies are required beyond the Python Standard Library.

## Usage

### Importing the Module

```python
from rosetta_finder import RosettaFinder, RosettaBinary
```

### Finding a Rosetta Binary

```python
# Initialize the finder (optional custom search path)
finder = RosettaFinder(search_path='/custom/path/to/rosetta/bin')

# Find the binary (default is 'rosetta_scripts')
rosetta_binary = finder.find_binary('rosetta_scripts')

# Access binary attributes
print(f"Binary Name: {rosetta_binary.binary_name}")
print(f"Mode: {rosetta_binary.mode}")
print(f"OS: {rosetta_binary.os}")
print(f"Compiler: {rosetta_binary.compiler}")
print(f"Release: {rosetta_binary.release}")
print(f"Full Path: {rosetta_binary.full_path}")
```

### Example Output

```
Binary Name: rosetta_scripts
Mode: mpi
OS: linux
Compiler: gcc
Release: release
Full Path: /custom/path/to/rosetta/bin/rosetta_scripts.mpi.linuxgccrelease
```

## Environment Variables

The `RosettaFinder` searches the following directories by default:

1. The path specified in the `ROSETTA_BIN` environment variable.
2. `ROSETTA3/bin`
3. `ROSETTA/main/source/bin/`
4. A custom search path provided during initialization.

Set the `ROSETTA_BIN` environment variable to include your custom binary directory:

```bash
export ROSETTA_BIN=/path/to/your/rosetta/bin
```

## API Reference

### `RosettaFinder` Class

- **Initialization**

  ```python
  RosettaFinder(search_path=None)
  ```

  - `search_path` (optional): A custom directory to include in the search paths.

- **Methods**

  - `find_binary(binary_name='rosetta_scripts')`

    Searches for the specified binary and returns a `RosettaBinary` instance.

    - `binary_name` (optional): Name of the binary to search for.

    - **Raises**:
      - `FileNotFoundError`: If the binary is not found.
      - `EnvironmentError`: If the OS is not Linux or macOS.

### `RosettaBinary` Dataclass

- **Attributes**

  - `dirname`: Directory where the binary is located.
  - `binary_name`: Base name of the binary.
  - `mode`: Build mode (`static`, `mpi`, `default`, or `None`).
  - `os`: Operating system (`linux` or `macos`).
  - `compiler`: Compiler used (`gcc` or `clang`).
  - `release`: Build type (`release` or `debug`).

- **Properties**

  - `filename`: Reconstructed filename based on the attributes.
  - `full_path`: Full path to the binary executable.

- **Class Methods**

  - `from_filename(dirname: str, filename: str)`

    Creates an instance by parsing the filename.

    - **Raises**:
      - `ValueError`: If the filename does not match the expected pattern.

## Running Tests

The project includes unit tests using Python's `unittest` framework.

### Running Tests

1. Navigate to the project directory:

   ```bash
   cd rosetta_finder
   ```

2. Run the tests:

   ```bash
   python -m unittest discover tests
   ```

### Test Coverage

The tests cover:

- Parsing valid and invalid filenames with `RosettaBinary`.
- Finding binaries with `RosettaFinder`, including scenarios where binaries are found or not found.
- OS compatibility checks.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for bug reports and feature requests.

## License

This project is licensed under the MIT License.

## Acknowledgements

- **Rosetta Commons**: The Rosetta software suite for the computational modeling and analysis of protein structures.

## Contact

For questions or support, please contact:

- **Name**: Yinying Yao
- **Email**:yaoyy.hi(a)gmail.com
