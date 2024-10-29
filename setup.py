from setuptools import setup, find_packages

setup(
	name='project1',
	version='1.0',
	author='Venkat Lokesh V',
	authour_email='vvejendla@ufl.edu',
	packages=find_packages(exclude=('tests', 'docs')),
	setup_requires=['pytest-runner'],
	tests_require=['pytest']	
)
