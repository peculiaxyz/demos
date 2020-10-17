@ECHO OFF
ECHO "Distributing package to the Production Python Package Index"

REM pipenv shell
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
python -m pip install --upgrade twine

ECHO Set up done, now building and uploading..
python setup.py sdist bdist_wheel
python -m twine upload  --skip-existing dist/*

