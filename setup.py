from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    # $ pip install wombat
    name='wombat',
    version='0.0.1',
    description='A wrapper tool for creating CWL tools to run on washington university Compute1 via Cromwell',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/estorrs/wombat',
    author='Erik Storrs',
    author_email='epstorrs@gmail.com',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='Cromwell CWL wombat washu washington university compute1',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        ],
    include_package_data=True,

#     entry_points={
#         'console_scripts': [
#             'wombat=wombat.wombat:main',
#         ],
#     },
)
