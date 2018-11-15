from setuptools import setup

setup(name='powersimdata',
      version='0.1',
      description='Power Simulation Data',
      url='https://github.com/intvenlab/powersimdata',
      author='Kaspar Mueller',
      author_email='kmueller@intven.com',
      packages=setuptools.find_packages(),
      package_data={'powersimdata':['input/data/usa/*']},
      zip_safe=False)
