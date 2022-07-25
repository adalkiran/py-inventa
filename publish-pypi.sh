pip install --upgrade build twine
python3 -m build && twine upload dist/* --config-file /home/.pypirc