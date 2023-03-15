from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
import uuid
import os
import traceback
CACHE_DIR = os.environ.get('CACHE_DIR')

from util import get_processors
from .. import preprocessing

keyword = "processors"
Processors = get_processors(preprocessing)
uuid_field = fields.String()
uuid_field.__schema_format__ = 'uuid'

namespace = Namespace('preprocessing', 'Preprocessing the raw data')

parameter_model = namespace.model('Parameter', {
  'name': fields.String(example="Max voltage"),
  'value': fields.Float(example=1600),
  'std_dev': fields.Float(example=12),
  'unit': fields.String(example="mV"),
  'str_value': fields.String(description="only used if the parameter does not have a numeric value. else `none`"),
})

result_model = namespace.model('Result', {
  'metadata': fields.List(fields.Nested(parameter_model)),
  'processed_uuid': uuid_field,
  'type': fields.String,
})
  

preprocessed_model = namespace.model('Preprocessed', {
    'info': fields.String(
        description='Freetext comment to convey status information/error messages of the processing tool: usually left blank'
    ),
    'results': fields.List(fields.Nested(result_model, skip_none=True))
})

upload_parser = namespace.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)

preprocessed_example = {'info': ''}

@namespace.route('/<measurement_type>')
@namespace.param('measurement_type', 'The type of measurement. Possible values are reported by `/preprocessing/types` ')
@namespace.expect(upload_parser)
class Preprocess(Resource):
    @namespace.marshal_with(preprocessed_model)
    @namespace.response(500, 'Internal Server error')
    @namespace.response(400, 'Wrong Request')
    def post(self, measurement_type):
        '''Do the preprocessing for different kinds of measurements. 
        Please provide the raw file from the tool. In the future a second endpoint will be available to list the available measurement types.
        The processed data including metadata and compressed raw data will be returned. If the request fails in an aticipated way the error is described in `info`'''
        args = upload_parser.parse_args()

        if measurement_type not in Processors:
          return {'info': f'given type not known: Know types are {Processors.keys()}'}, 400

        uploaded_file = args['file']  # Get the file
        
        try:
          res = Processors[measurement_type].run(uploaded_file) #run the processing
          if len(res) == 2:
            res, errors = res
          else:
            errors = {}
        except Exception as e: 
          traceback.print_exc()
          return {'results': {}, 'info': str(e)}, 400
        for r in res:  #save the result and give it a uuid
          df = r['processed']
          #print(df)
          r_uuid = uuid.uuid4()
          df.to_pickle(f"{CACHE_DIR}/{r_uuid}.pkl")
          r['processed_uuid'] = str(r_uuid)
          r['type'] = measurement_type
        return {'results': res, 'info': errors if len(errors) else 'OK'}, 200

types = list(Processors.keys())

@namespace.route('/types')
class Types(Resource):
    @namespace.response(500, 'Internal Server error')
    @namespace.response(200, 'List of Measurement Types is returned', fields.List(fields.String, example=types))
    def get(self):
        '''A list of possible measurement types. Automatically updated when a measurement type is added.'''
        return types, 200
    get.__doc__ += f" \nCurrently: `{types}`"