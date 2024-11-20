import json
import shutil
import pathlib
import subprocess

from shapely.geometry import shape, Point
from shapely import simplify
from csvw.dsv import reader, UnicodeWriter
from clldutils.jsonlib import dump
from clldutils.markup import add_markdown_text
from cldfbench import Dataset as BaseDataset
from cldfgeojson import feature_collection
from cldfgeojson import MEDIA_TYPE
from cldfgeojson.create import aggregate, merged_geometry


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "allen2016resource"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    def cmd_download(self, args):
        # turn geopackage into geojson
        # turn polygon list into etc/polygons.csv
        # make sure list is complete and polygons are valid.
        sdir = self.dir.parent / 'glottography-data' / self.id
        shutil.copy(sdir / 'source' / '{}.bib'.format(sdir.name), self.raw_dir / 'sources.bib')
        # We want a valid geopackage:
        subprocess.check_call([
            'ogr2ogr',
            str(self.raw_dir / 'dataset.geojson'),
            str(sdir / '{}_raw.gpkg'.format(sdir.name)),
            '-t_srs', 'EPSG:4326',
            '-s_srs', 'EPSG:3857',
        ])
        polys = {
            f['properties']['polygon_id']: f for
            f in self.raw_dir.read_json('dataset.geojson')['features']}
        assert all(shape(f['geometry']).is_valid for f in polys.values())
        if not self.etc_dir.joinpath('polygons.csv').exists():
            with UnicodeWriter(self.etc_dir / 'polygons.csv') as w:
                #polygon_id,name,glottocode,reference,year,map_name_full,map_image_file,url,lon,lat,note
                for i, row in enumerate(
                    reader(sdir / '{}_glottocode_to_polygons.csv'.format(sdir.name), dicts=True),
                    start=1,
                ):
                    assert sdir.name == row.pop('reference')
                    if i == 1:
                        w.writerow(row.keys())
                    w.writerow(row.values())
                    pid = int(row['polygon_id'])
                    assert pid in polys, row['polygon_id']
                    assert shape(polys[pid]['geometry']).contains(
                        Point(float(row['lon']), float(row['lat'])))
            assert i == len(polys)

    def iter_polys(self):
        md = {int(row['polygon_id']): row for row in self.etc_dir.read_csv('polygons.csv', dicts=True)}

        for f in self.raw_dir.read_json('dataset.geojson')['features']:
            pid = f['properties']['polygon_id']
            #
            # FIXME: possibly need to update properties
            #
            yield (pid, f, md[pid]['glottocode'] or None)

    def cmd_makecldf(self, args):
        # Write three sets of shapes:
        # 1. The shapes as they are in the source, aggregated by shape label, including
        #    fine-grained Glottocode(s) as available.
        # 2. The shapes aggregated by language-level Glottocodes.
        # 3. The shapes aggregated by family-level Glottocodes.

        self.schema(args.writer.cldf)

        polys = self.iter_polys()
        features = []
        for pid, f, gc in polys:
            f['properties'] = {
                k: v for k, v in f['properties'].items()
                if k in {'polygon_id', 'name', 'year', 'map_name_full'}}
            if gc:
                f['properties']['cldf:languageReference'] = gc
            features.append(f)
            args.writer.objects['ContributionTable'].append(dict(
                ID=pid,
                Name=f['properties']['name'],
                Glottocode=gc or None,
                #Source=['ecai', 'wurm_and_hattori'],
                Media_ID='shapes',
                Map_Name=f['properties']['map_name_full'],
            ))
        #
        # FIXME: add collection-level properties!
        #
        dump(dict(
            type='FeatureCollection',
            properties=dict(description=self.metadata.description),
            features=features), self.cldf_dir / 'shapes.geojson')
        args.writer.objects['MediaTable'].append(dict(
            ID='shapes',
            Name='Areas depicted in the source',
            Media_Type=MEDIA_TYPE,
            Download_URL='shapes.geojson',
        ))

        lids = None
        for ptype in ['language', 'family']:
            label = 'languages' if ptype == 'language' else 'families'
            p = self.cldf_dir / '{}.geojson'.format(label)
            features, languages = aggregate(
                self.iter_polys(), args.glottolog.api, level=ptype, buffer=0.005, opacity=0.5)
            dump(feature_collection(
                features,
                title='Speaker areas for {}'.format(label),
                description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype)),
                p,
                indent=2)

            for (glang, pids, family), f in zip(languages, features):
                if lids is None or (glang.id not in lids):  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=glang.id,
                        Name=glang.name,
                        Glottocode=glang.id,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Contribution_IDs=map(str, pids),
                        Speaker_Area=p.stem,
                        #Glottolog_Languoid_Level=ptype,
                        #Family=family,
                    ))
            args.writer.objects['MediaTable'].append(dict(
                ID=p.stem,
                Name='Speaker areas for {}'.format(label),
                Description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype),
                Media_Type=MEDIA_TYPE,
                Download_URL=p.name,
            ))
            lids = {gl.id for gl, _, _ in languages}


    def cmd_readme(self, args):
        # Write the (simplified) outline of all shapes to the README (if < 1MB or similar)
        shp = shape(merged_geometry([f for _, f, _ in self.iter_polys()]))
        shp = simplify(shp, 0.1)
        f = json.dumps(dict(type='Feature', geometry=shp.__geo_interface__))
        print(len(f))
        return add_markdown_text(
            BaseDataset.cmd_readme(self, args),
            """

### Coverage

```geojson
{}
```
""".format(f),
            'Description')

    def schema(self, cldf):
        cldf.add_component('MediaTable')
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Contribution_IDs',
                'separator': ' ',
                'dc:description':
                    'List of identifiers of shapes that were aggregated '
                    'to create the shape referenced by Speaker_Area.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'
            },
            {
                'name': 'Speaker_Area',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#speakerArea'
            })
        t = cldf.add_component(
            'ContributionTable',
            {
                "datatype": {
                    "base": "string",
                    "format": "[a-z0-9]{4}[1-9][0-9]{3}"
                },
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#glottocode",
                "valueUrl": "http://glottolog.org/resource/languoid/id/{Glottocode}",
                "name": "Glottocode",
                'dc:description':
                    'References a Glottolog languoid most closely matching linguistic entity '
                    'described by the shape.',
            },
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'
            },
            {
                'name': 'Media_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
                'dc:description': 'Shapes are linked to GeoJSON files that store the geo data.'
            },
            {
                'name': 'Map_Name',
                'dc:description': 'Name of the map as given in the source publication.'
            }
        )
        t.common_props['dc:description'] = \
            ('We list the individual shapes from the source dataset as contributions in order to '
             'preserve the original metadata.')
