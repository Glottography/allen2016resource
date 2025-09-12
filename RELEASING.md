# Releasing the dataset

## Recreate the raw data from glottography-data

```shell
cldfbench download cldfbench_allen2016resource.py
```

## Recreate the CLDF data

```shell
cldfbench makecldf cldfbench_allen2016resource.py --glottolog-version v5.2
cldfbench cldfreadme cldfbench_allen2016resource.py
cldfbench zenodo cldfbench_allen2016resource.py
cldfbench readme cldfbench_allen2016resource.py
```

## Validation

```shell
cldf validate cldf
```

```shell
cldfbench geojson.validate cldf
```

```shell
cldfbench geojson.glottolog_distance cldf
```

| ID | Distance | Contained | NPolys |
|:---------|-----------:|:------------|---------:|
| baym1241 | 0.41 | False | 1 |
| coas1301 | 0.00 | True | 1 |
| nise1244 | 0.64 | False | 1 |
| nort2951 | 0.00 | True | 1 |
| nort2952 | 0.00 | True | 1 |
| patw1250 | 0.00 | True | 1 |
| plai1259 | 0.12 | False | 1 |
| wapp1239 | 0.18 | False | 1 |
| wint1259 | 0.00 | True | 1 |
| yana1271 | 0.54 | False | 1 |
| yoku1256 | 0.46 | False | 1 |
