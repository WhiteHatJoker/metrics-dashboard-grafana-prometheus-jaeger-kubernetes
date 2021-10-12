from flask import Flask, render_template, request, jsonify
import logging, os, random, opentracing

from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

from jaeger_client import Config
from flask_opentracing import FlaskTracer

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
tracing = FlaskTracer(jaeger_tracer, True, app)
flask_head_tracing = tracing.get_span()

@app.route('/')
def homepage():
    with opentracing.tracer.start_span("base-endpoint", child_of=flask_head_tracing) as span:
        return "Hello World"


@app.route('/api')
def my_api():
    with opentracing.tracer.start_span("api-endpoint", child_of=flask_head_tracing) as span:
        answer = "something"
        span.set_tag("answer", answer)
        return jsonify(repsonse=answer)

@app.route('/star', methods=['POST'])
def add_star():
    with opentracing.tracer.start_span("star-endpoint", child_of=flask_head_tracing) as span:
        try:
            star = mongo.db.stars
            name = request.json['name']
            distance = request.json['distance']
            star_id = star.insert({'name': name, 'distance': distance})
            new_star = star.find_one({'_id': star_id })
            output = {'name' : new_star['name'], 'distance' : new_star['distance']}
            span.set_tag("output", output)
            return jsonify({'result' : output})
        except:
            span.set_tag("output", "issue with database connection on star endpoint")

@app.route('/errors')
def error_message():
    errors_choice = [500,503]
    return jsonify({"error": "Fake Error",}), random.choice(errors_choice)

if __name__ == "__main__":
    app.run()
