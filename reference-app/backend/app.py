from flask import Flask, render_template, request, jsonify
import logging, os, random

from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

from jaeger_client import Config
from flask_opentracing import FlaskTracing

import pymongo
from flask_pymongo import PyMongo

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
metrics = GunicornInternalPrometheusMetrics(app)
metrics.info('app_info', 'Backend Service', version='1.0.3')

app.config['MONGO_DBNAME'] = 'example-mongodb'
app.config['MONGO_URI'] = 'mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb'
mongo = PyMongo(app)

config = Config(
    config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
            'reporter_batch_size': 1,
        },
    service_name="backend"
)

jaeger_tracer = config.initialize_tracer()
tracing = FlaskTracing(jaeger_tracer, True, app)

@app.route('/')
def homepage():
    return "Hello World"


@app.route('/api')
def my_api():
    answer = "something"
    return jsonify(repsonse=answer)

@app.route('/star', methods=['POST'])
def add_star():
  star = mongo.db.stars
  name = request.json['name']
  distance = request.json['distance']
  star_id = star.insert({'name': name, 'distance': distance})
  new_star = star.find_one({'_id': star_id })
  output = {'name' : new_star['name'], 'distance' : new_star['distance']}
  return jsonify({'result' : output})

@app.route('/errors')
def error_message():
  errors_choice = [500,503]
  return jsonify({"error": "Fake Error",}), random.choice(errors_choice)

if __name__ == "__main__":
    app.run()
