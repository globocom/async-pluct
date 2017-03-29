from setuptools import setup, find_packages


setup(
    name='pluct',
    version='1.3.0',
    description='JSON Hyper Schema client',
    long_description=open('README.rst').read(),
    author='Lucas Stephanou',
    author_email='domluc@gmail.com',
    url='https://github.com/lucasts/async-pluct',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    packages=find_packages(exclude=('tests.*', 'tests')),
    include_package_data=True,
    install_requires=[
        'requests',
        'jsonschema',
        'jsonpointer',
    ],
)
