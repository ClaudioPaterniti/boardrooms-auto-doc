Copy default_refs.json into a new per-project file like lc.json and set the corresponding paths.
Launch like:
```
python gen_doc.py --refs lc
```

To allow visual rendering of table relations it is necessary to install Graphviz api:
```
pip install graphviz
```
and to download and install Graphviz:
- on Windows: official [site](https://graphviz.org/) (remeber to mark the option to set PATH env. variable)
- on Ubuntu 
```
sudo apt install graphviz
```
