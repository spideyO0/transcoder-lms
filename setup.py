from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
from setuptools.command.develop import develop

class CustomInstallCommand(install):
    """Customized setuptools install command - installs dependencies and patches Streamlit."""
    
    def run(self):
        # Proceed with the standard installation process
        install.run(self)
        
        # Run the patch script to modify Streamlit after installation
        try:
            subprocess.check_call([sys.executable, 'patch_streamlit.py'])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the patch script: {e}")
            sys.exit(1)

class CustomDevelopCommand(develop):
    """Customized setuptools install command - installs dependencies and patches Streamlit."""
    
    def run(self):
        # Proceed with the standard installation process
        
        # Run the patch script to modify Streamlit after installation
        try:
            subprocess.check_call([sys.executable, 'patch_streamlit.py'])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the patch script: {e}")
            sys.exit(1)
        install.run(self)


setup(
    name='abr-transcoder',  # Replace with your actual project name
    version='0.1',
    packages=find_packages(),  # Automatically find all packages in the current directory
    cmdclass={
        'develop': CustomDevelopCommand,
        'install': CustomInstallCommand,
    },
    install_requires=[
        'streamlit',  # Ensure Streamlit is listed here
        'ffmpeg-python',
        'numpy',
        'pydub',
        'requests',
        'flask',
        'flask_cors',
        'waitress',
        'setuptools',
        'wheel',
        # Add other dependencies as needed.
    ],
)
