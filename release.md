+ To build the package, use setuptools:

```bash
python setup.py sdist bdist_wheel
```

+ To upload the package to PyPI, use twine:

For the frsit time,
```bash
pip install twine       # if haven't done so
twine upload dist/*     # register an account in https://pypi.org/
```

For version, first upgrade in setup.py, then
```bash
twine upload --skip-existing dist/*  
```

+ To run the package in a command line
```bash
pip install openapi2tools # or, pip install --upgrade openapi2tools==<version>
openapi2tools <Your OpenAPI json> <Output python file name>
```