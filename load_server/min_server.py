import numpy as np
from flask import Flask
from flask_restplus import Api, Resource, fields

app = Flask(__name__)

api = Api(app, version='1.0', title='CPU Loader', description='loading app',
          contact_email='roym@technion.ac.il', contact='Roy Mitrany')
ns = api.namespace('load', description='CPU Loader')

srv_state = api.model('ServerState', {
    'completed_tasks': fields.String(required=True, description='Number of completed tasts since start'),
    'current_tasks': fields.String(required=True, description='Number of tasks that are currently running'),
    'duration': fields.String(required=False, description='Duration of last task')})

def load_cpu(level):
	num = level*1000000
	list = range(0,num)
	for i in list:
		fl = float(i/num)
		tfl = np.tanh(fl)

@ns.route('/ping')
class Ping(Resource):
    @ns.doc('test_liveness')
    @ns.response(200, 'Success')
    def hello_world():
       """Check status"""
       return 'Hello, Loader!'

@ns.route('/create_load/<int:level>')
@ns.param('level', description='Load Level')
@ns.response(400, 'Invalid operation')
class LoadLevel(Resource):
    @ns.doc('load_cpu')
    @ns.marshal_with(srv_state)
    @ns.response(200, 'Success')
    def get(self, level):
        """Load CPU by level. The load will be about level*2 seconds """
        load_cpu(level)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
