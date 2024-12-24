from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
import os
from setuptools.command.develop import develop

def ensure_pip():
    """Ensure that pip is available in the current Python environment."""
    try:
        import pip  # noqa: F401
    except ImportError:
        print("Pip not found. Bootstrapping pip with ensurepip...")
        import ensurepip
        ensurepip.bootstrap()

class CustomInstallCommand(install):
    """Customized setuptools install command - installs dependencies and patches Streamlit."""

    def run(self):
        try:
            # Ensure pip is available
            ensure_pip()

            # Install runtime dependencies first
            print("Installing runtime dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

            # Proceed with the standard installation process
            print("Running the standard installation process...")
            install.run(self)

            # Run the patch script to modify Streamlit after installation
            print("Running Streamlit patch...")
            subprocess.check_call([sys.executable, "patch_streamlit.py"])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the patch script: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)


class CustomDevelopCommand(develop):
    """Customized setuptools develop command - installs dependencies and patches Streamlit."""

    def run(self):
        try:
            # Ensure pip is available
            ensure_pip()

            # Install runtime dependencies first
            print("Installing runtime dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

            # Proceed with the standard development installation process
            print("Running the standard development process...")
            develop.run(self)

            # Run the patch script to modify Streamlit after installation
            print("Running Streamlit patch...")
            subprocess.check_call([sys.executable, "patch_streamlit.py"])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the patch script: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)


setup(
    name="abr-transcoder",  # Replace with your actual project name
    version="0.1",
    packages=find_packages(),  # Automatically find all packages in the current directory
    cmdclass={
        "develop": CustomDevelopCommand,
        "install": CustomInstallCommand,
    },
    install_requires=[
        "streamlit",  # Ensure Streamlit is listed here
        "ffmpeg-python",
        "numpy",
        "pydub",
        "requests",
        "flask",
        "flask_cors",
        "waitress",
        "setuptools",
        "wheel",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
        ],
    },
    python_requires=">=3.6",  # Ensure Python compatibility
)