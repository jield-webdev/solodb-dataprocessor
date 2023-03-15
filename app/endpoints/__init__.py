# blueprints/documented_endpoints/__init__.py
from flask import Blueprint
from flask_restx import Api
from endpoints.preprocessing import namespace as preprocessing
from endpoints.postprocessing import namespace as postprocessing

blueprint = Blueprint('documented_api', __name__)

api_extension = Api(
    blueprint,
    title='SoloDB Processing Api',
    version='1.0',
    description='''API to ingest, pre- and postprocess measurement data of various sources.
        In this context postprocessing refers to generating graphs from the processed data, to be displayed in SoloDB''',
    doc='/doc'
)

api_extension.add_namespace(preprocessing)
api_extension.add_namespace(postprocessing)