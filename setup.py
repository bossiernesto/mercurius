from setuptools import setup, find_packages

setup(name="mercurius",
      version="0.1.0",
      description="HTTP/S and FTP Local Proxy",
      author="Ernesto Bossi",
      author_email="bossi.ernestog@gmail.com",
      url="https://github.com/bossiernesto/mercurius",
      license="BSD",
      py_modules=find_packages(exclude=('test')),
      keywords="HTTP Proxy",
      classifiers=["Development Status :: 2 - Pre-Alpha",
                   "Environment :: Console",
                   "License :: OSI Approved :: BSD License"],
      requires=["http-parser", "pyparsing"]
)