from setuptools import setup

version = '0.0.1'

setup(
    name='azure-transcript',
    version=version,
    description='A Python library for interacting with Azure Transcription API',
    author='Daniel Cuznetov',
    author_email='danielcuznetov04@gmail.com',
    packages=['azure_transcript'],
    install_requires=['django'],
)