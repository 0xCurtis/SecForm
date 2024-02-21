from setuptools import setup, find_packages

setup(
name='SecForm',
version='0.1.0',
author='0xCu',
author_email='curtis1337wastaken@protonmail.com',
description='SecForm is a lightweight package to get the latest fillings from the SEC website.',
packages=find_packages(),
classifiers=[
'Programming Language :: Python :: 3',
'License :: OSI Approved :: MIT License',
'Operating System :: OS Independent',
],
python_requires='>=3.6',
)