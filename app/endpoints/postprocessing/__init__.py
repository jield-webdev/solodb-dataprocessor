from flask_restx import Namespace, Resource, reqparse, fields
import os
import pandas as pd
import json
from flask import send_file
CACHE_DIR = os.environ.get('CACHE_DIR')

from util import get_processors
from .. import postprocessing

keyword = "processors"
Processors = get_processors(postprocessing) #not too beautiful in combination with multiprocessing

namespace = Namespace('postprocessing', 'Converting the processed data (stored in SoloDB) into a human readable graph')

graphrequest = namespace.schema_model('Graphrequest', { #request for graphing
    'required': ['processed_uuid'],
    'properties': {
        'processed_uuid': {
            'type': 'array',
            'items': {
              'type': 'string',
              'format': 'uuid',
              'example': '0620a1b4-e6ca-4437-9844-a01166eeb6b7'
            },
        },
        'figsize_x': {
            'type': 'number',
            'example': '5'
        },
        'figsize_y': {
            'type': 'number',
            'example': 3
        },
        'config': {
            'type': 'object'
        }
    },
    'type': 'object'
})

parser = reqparse.RequestParser()
parser.add_argument('processed_uuid', action="append", required=True, 
  help='Data previously returned from preprocess')
parser.add_argument('figsize_x', type=float, default=3)
parser.add_argument('figsize_y', type=float, default=2)
parser.add_argument('config', type=str, required=False, help='''\
Configuration dictionary (as json) can be used to indicate a special configuration.\
Should probably be user defined? (e.g. to identify parameter of interest)
''')

def cache_hit(uuid):
  '''Tests whether uuid is in cache'''
  return os.path.exists(f"{CACHE_DIR}/{uuid}.pkl")

@namespace.route('/<analysis_type>.png')
@namespace.param('analysis_type', 'The type of analysis. Possible values are reported by `/postprocessing/types` ')
@namespace.expect(parser)
class Postprocess(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(410, 'Gone: Cache Miss')
    @namespace.response(400, 'Bad Request')
    @namespace.response(200, description='return generated diagram as PNG image file.')
    @namespace.produces(['image/png'])
    def get(self, analysis_type):
        '''Generates a plot of the given data and config. It is assumed that '''
        if analysis_type not in Processors:
          return {'info': f'given type not known: Know types are {Processors.keys()}'}, 400

        args = parser.parse_args()
        try:
          args["config"] = json.loads(args["config"])
        except:
          return "config has to be a valid json object", 400
        dfs = []
        for p_uuid in args['processed_uuid']:
          if not cache_hit(p_uuid):
            return "Miss", 410
          df = pd.read_pickle(f"{CACHE_DIR}/{p_uuid}.pkl")
          dfs.append(df)
        res = Processors[analysis_type].run(dfs, args)
        print(res)
        return res

types = {key: val.input_type for key, val in Processors.items()}
inv_types = {}
for k, v in types.items():
  inv_types[v] = inv_types.get(v, []) + [k]

wild = fields.Wildcard(fields.List(fields.String), example=inv_types)
@namespace.route('/types')
class Types(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(200, 'Success', wild)
    def get(self):
        '''A dict of possible plot types for each input type. Automatically updated when a plot type is added.'''
        return inv_types, 200
    get.__doc__ += f" \nCurrently: `{inv_types}`"

@namespace.route('/types/<analysis_type>')
@namespace.param('analysis_type', 'The type of analysis. Possible values are reported by `/postprocessing/types` ')
class TypeInfo(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(200, 'Success')
    @namespace.response(400, 'Type not present')
    def get(self, analysis_type):
        '''A dict with information about an `analysis_type`'''
        if not analysis_type in Processors:
          return "Not present", 400

        p = Processors[analysis_type]
        return {
          key: getattr(p, key, "") for key in ['link', 'input_type', 'description', 'example_config']
        }, 200

uuid_parser = namespace.parser()
uuid_parser.add_argument('uuid', type=str, help='the `uuid` of the requested resource')

@namespace.route('/cachetest')
class CacheValid(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(200, 'Success: Cache Hit')
    @namespace.response(410, 'Gone: Cache Miss')
    @namespace.expect(uuid_parser)
    def get(self):
        '''Is the cached file still present?'''
        args = uuid_parser.parse_args()
        if cache_hit(args['uuid']):
          return "Success", 200
        return "Miss", 410


@namespace.route('/download')
class Download(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(200, 'Success: Processed Data File')
    @namespace.response(410, 'Gone: Cache Miss')
    @namespace.expect(uuid_parser)
    def get(self):
        '''Download File from Cache if present'''
        args = uuid_parser.parse_args()
        uuid = args['uuid']
        if not cache_hit(uuid):
          return "Miss", 410
        return send_file(os.path.abspath(f"{CACHE_DIR}/{uuid}.pkl"))

