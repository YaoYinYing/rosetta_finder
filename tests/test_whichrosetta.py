import unittest
import subprocess
import os
import sys
import tempfile
import shutil
from unittest.mock import patch


class TestWhichRosetta(unittest.TestCase):

    def test_integration_whichrosetta_success(self):
        # Create a temporary directory to act as ROSETTA_BIN
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a mock binary file
            binary_name = "rosetta_scripts.linuxgccrelease"
            binary_path = os.path.join(temp_dir, binary_name)
            with open(binary_path, "w") as f:
                f.write("# Mock Rosetta binary")

            # Set the ROSETTA_BIN environment variable to the temp directory
            env = os.environ.copy()
            env["ROSETTA_BIN"] = temp_dir

            # Patch sys.platform to 'linux'
            with patch("sys.platform", "linux"):
                # Invoke the whichrosetta command
                result = subprocess.run(
                    ["whichrosetta", "rosetta_scripts"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )

                # Check that the command was successful
                self.assertEqual(result.returncode, 0)
                expected_output = f"{binary_path}\n"
                self.assertEqual(result.stdout, expected_output)
                self.assertEqual(result.stderr, "")
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def test_dockerized_whichrosetta_success(self):
        # Create a temporary directory to act as ROSETTA_BIN
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a mock binary file
            binary_name = "rosetta_scripts"
            binary_path = os.path.join(temp_dir, binary_name)

            with open(binary_path, "w") as f:
                f.write("# Mock Rosetta binary")

            os.chmod(binary_path, 755)

            # Set the ROSETTA_BIN environment variable to the temp directory
            env = os.environ.copy()
            env["PATH"] = temp_dir + ":" + env["PATH"]

            for key in os.environ.keys():
                if "ROSETTA" in key:
                    del env[key]

            # Patch sys.platform to 'linux'
            with patch("sys.platform", "linux"):
                # Invoke the whichrosetta command
                result = subprocess.run(
                    ["whichrosetta", "rosetta_scripts"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )

                # Check that the command was successful
                print(result.stderr)
                print(result.stdout)
                self.assertEqual(result.returncode, 0)
                expected_output = f"{binary_path}\n"
                self.assertEqual(result.stdout, expected_output)
                self.assertEqual(result.stderr, "")
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def test_integration_whichrosetta_not_found(self):
        # Create a temporary directory to act as ROSETTA_BIN
        temp_dir = tempfile.mkdtemp()
        try:
            # Set the ROSETTA_BIN environment variable to the temp directory
            env = os.environ.copy()
            env["ROSETTA_BIN"] = temp_dir

            # Patch sys.platform to 'linux'
            with patch("sys.platform", "linux"):
                # Invoke the whichrosetta command
                result = subprocess.run(
                    ["whichrosetta", "rosetta_scripts"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )

                # Check that the command failed
                self.assertNotEqual(result.returncode, 0)
                expected_error = "rosetta_scripts binary not found in the specified paths.\n"
                self.assertEqual(result.stdout, "")
                self.assertIn(expected_error, result.stderr)
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    # def test_whichrosetta_unsupported_os(self):
    #     # Create a temporary directory to act as ROSETTA_BIN
    #     temp_dir = tempfile.mkdtemp()
    #     try:
    #         # Create a mock binary file
    #         binary_name = "rosetta_scripts.linuxgccrelease"
    #         binary_path = os.path.join(temp_dir, binary_name)
    #         with open(binary_path, "w") as f:
    #             f.write("# Mock Rosetta binary")

    #         # Set the ROSETTA_BIN environment variable
    #         env = os.environ.copy()
    #         env["ROSETTA_BIN"] = temp_dir

    #         # Patch sys.platform to 'win32'
    #         with patch("sys.platform", "win32"):
    #             # Invoke the whichrosetta command
    #             result = subprocess.run(
    #                 ["whichrosetta", "rosetta_scripts"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
    #             )

    #             # Check that the command failed due to unsupported OS
    #             self.assertNotEqual(result.returncode, 0)
    #             expected_error = "Unsupported OS. This script only runs on Linux or macOS.\n"
    #             self.assertEqual(result.stdout, "")
    #             self.assertIn(expected_error, result.stderr)

    #     finally:
    #         # Clean up the temporary directory
    #         shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
