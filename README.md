The documentation is populated by parsing the views' notebooks and the pbix serialization generated with Tabular Editor or with [PbixSerializer](https://github.com/ClaudioPaterniti/PbixSerializer) (in this case the option '-s sloth' should be used).

Copy default_refs.json into a new per-project file, for example project_name.json, and set the corresponding paths.
Launch with:
```
python gen_doc.py -r project_name
```
For command line options run:
```
python gen_doc.py -h
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
