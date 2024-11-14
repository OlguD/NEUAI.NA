from setuptools import setup, find_packages

setup(
    name='NEUAI.NA',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'face_recognition',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'face_detection=face_detection:main',
        ],
    },
)