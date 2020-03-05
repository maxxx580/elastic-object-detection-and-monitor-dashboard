import logging

import botocore
from flask import Blueprint, abort, jsonify, request

import manager
from manager.aws import autoscale, instance_manager

bp = Blueprint("workers", __name__, url_prefix='/workers')
logger = logging.getLogger('manager')


@bp.route('/cpu', methods=['GET'])
def get_worker_cpu_usage():

    try:
        cpu_usage_data = manager.ec2_manager.get_cpu_utilization()
        time_stamps, datapoints = data_convert_helper(cpu_usage_data)
        return jsonify({
            'isSuccess': True,
            'timestamps': time_stamps,
            'datapoints': datapoints
        })
    except Exception as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/traffic', methods=['GET'])
def get_worker_inbount_traffic():
    try:
        inbound_traffic = manager.ec2_manager.get_instance_inbound_rate()
        time_stamps, datapoints = data_convert_helper(inbound_traffic)
        return jsonify({
            'isSuccess': True,
            'timestamps': time_stamps,
            'datapoints': datapoints
        })
    except Exception as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/pool_sizes', methods=['GET'])
def get_worker_pool_size():
    sizes = [s[0] for s in manager.worker_pool_size]
    timestamps = [t[1] for t in manager.worker_pool_size]
    return jsonify({
        'sizes': sizes,
        'timestamps': timestamps
    })


@bp.route('/', methods=['GET', 'POST', 'DELETE'])
def workers():
    try:
        if request.method == 'GET':
            instances = manager.ec2_manager.get_instances()
            return jsonify({
                'isSuccess': True,
                'data': instances
            })
        elif request.method == 'POST':
            instance = manager.auto_scaler.scale_up()
            return jsonify({
                'isSuccess': True,
                'data': instance
            })

        elif request.method == 'DELETE':
            data = request.get_json()
            if data:
                manager.auto_scaler.scale_down(data['instance_id'])
            else:
                manager.auto_scaler.scale_down()
            return jsonify({
                'isSuccess': True,
            })
        else:
            abort(405)

    except botocore.exceptions.ClientError as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


def data_convert_helper(response):
    time_stamps = [datapoint[0] for datapoint in response]
    datapoints = [datapoint[1] for datapoint in response]
    return [time_stamps, datapoints]
