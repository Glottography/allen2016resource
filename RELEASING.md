# Releasing the dataset

```shell
cldfbench download cldfbench_allen2016resource.py
```
```shell
cldfbench makecldf cldfbench_allen2016resource.py --glottolog-version v5.1
cldf validate cldf
cldfbench cldfreadme cldfbench_allen2016resource.py
cldfbench zenodo cldfbench_allen2016resource.py
cldfbench readme cldfbench_allen2016resource.py
```
