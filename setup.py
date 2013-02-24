import os
from setuptools import setup


root = os.path.dirname(__file__)


setup(
    name='ec2price',
    version='0.0.1',
    description='EC2 Price Service',
    long_description=open(os.path.join(root, 'README.md')).read(),
    author='Alan Grosskurth',
    author_email='code@alan.grosskurth.ca',
    packages=[
        'ec2price',
    ],
    scripts=[
        'scripts/ec2price',
    ],
    test_suite='ec2price.tests',
    include_package_data=True,
    install_requires=open(os.path.join(root, 'requirements.txt')).readlines(),
    zip_safe=False,
)
