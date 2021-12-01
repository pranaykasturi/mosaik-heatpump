from setuptools import setup, find_packages
import os

setup(
    name='mosaik-heatpump',
    version='0.1.0',
    author='Pranay Kasturi',
    author_email='mosaik@offis.de',
    description='Mosaik-heatpump provides a model of a residential heatpump system',
    long_description=(open('README.rst', encoding='utf-8').read() + '\n\n' +
                      open('CHANGES.txt', encoding='utf-8').read() + '\n\n' +
                      open('AUTHORS.txt', encoding='utf-8').read()),
    long_description_content_type='text/x-rst',
    url='https://gitlab.com/mosaik/components/energy/mosaik-heatpump',
    install_requires=[
        'mosaik-api>=3.0',
        'tespy>=0.4.2',
        'jsonpickle'
    ],
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    py_modules=['mosaik_heatpump'],
    entry_points={
        'console_scripts': [
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
