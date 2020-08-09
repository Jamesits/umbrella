from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='umbrella',
   version='0.0.1',
   description='It backs up your codebase, effectively protects you when the cloud turns in to useless water.',
   license="MIT License",
   long_description=long_description,
   long_description_content_type="text/markdown",
   author='James Swineson',
   author_email='github@public.swineson.me',
   url="https://github.com/Jamesits/Umbrella",
   packages=['umbrella'],  #same as name
   install_requires=[],
   entry_points = {
      'console_scripts': [
          'umbrella=umbrella:main'
      ]
   }
)