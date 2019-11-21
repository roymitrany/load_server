import numpy as np
from flask import Flask
from flask_restplus import Api, Resource, fields
import time
import argparse

counter = 0
num_of_tasks = 0
app = Flask(__name__)

api = Api(app, version='1.0', title='CPU Loader', description='loading app',
          contact_email='roym@technion.ac.il', contact='Roy Mitrany')
ns = api.namespace('load', description='CPU Loader')

srv_state = api.model('ServerState', {
    'completed_tasks': fields.String(required=True, description='Number of completed tasts since start'),
    'current_tasks': fields.String(required=True, description='Number of tasks that are currently running'),
    'duration': fields.String(required=False, description='Duration of last task')})

def load_cpu(level):
    global num_of_tasks
    num = level*100000
    a_list = range(0,num)
    num_of_tasks += 1
    for i in a_list:
        fl = float(i/num)
        tfl = np.tanh(fl)
    num_of_tasks -= 1


@ns.route('/create_load/<int:level>')
@ns.param('level', description='Load Level')
@ns.response(400, 'Invalid operation')
class LoadLevel(Resource):
    # Trying to define a static variable
    #counter = 0
    @ns.doc('load_cpu')
    @ns.marshal_with(srv_state)
    @ns.response(200, 'Success')
    def get(self, level):
        """Load CPU by level. The load will be about level*2 seconds """
        global counter
        state = {}
        begin_ts = time.time ()
        load_cpu(level)
        end_ts = time.time ()
        duration_in_millis = int(1000*(end_ts-begin_ts))
        counter += 1
        state['completed_tasks'] = counter
        state['current_tasks'] = 1
        state['duration'] = str(duration_in_millis)
        return state




@ns.route('/ping')
class Ping(Resource):
    @ns.doc('test_liveness')
    @ns.marshal_with(srv_state)
    @ns.response(200, 'Success', srv_state)
    def get (self):
        global counter
        state = {'completed_tasks': counter, 'current_tasks': num_of_tasks}
        return state

@ns.route('/reset_tasks_counter')
class Ping(Resource):
    @ns.doc('reset the completed tasks counter. More convenient that restarting the server')
    @ns.marshal_with(srv_state)
    @ns.response(200, 'Success', srv_state)
    def get (self):
        global counter
        counter = 0
        state = {'completed_tasks': counter, 'current_tasks': num_of_tasks}
        return state

if __name__ == '__main__':
    parser = argparse.ArgumentParser (
        description='MMMMMMM',
    )
    parser.add_argument ('port', type=int)
    args = parser.parse_args ()
    port = args.port
    app.run(debug=True, host = '0.0.0.0', port=port)
