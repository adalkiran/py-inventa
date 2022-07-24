pip install --upgrade build twine
python3 -m build && twine upload --repository testpypi dist/* --config-file /home/.pypirc