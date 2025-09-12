import json
import shutil
import pathlib
import subprocess

from shapely.geometry import shape, Point
from shapely import simplify
from csvw.dsv import reader, UnicodeWriter
from clldutils.jsonlib import dump
from clldutils.markup import add_markdown_text
from cldfgeojson import feature_collection
from cldfgeojson import MEDIA_TYPE
from cldfgeojson.create import aggregate, merged_geometry

from pyglottography import Dataset as BaseDataset


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "allen2016resource"

