import pathlib

from pyglottography import Dataset as BaseDataset


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "allen2016resource"

