from setuptools import setup

setup(
    packages=['azure_transcribe', 'azure_transcribe.blob', 'azure_transcribe.fixtures', 'azure_transcribe.transcribe'],
    install_requires=['azure-storage-blob'],
)
