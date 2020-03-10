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
    except botocore.exceptions.ClientError as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/request_count', methods=['GET'])
def get_worker_inbount_traffic():
    try:
        request_count = manager.ec2_manager.get_elb_request_count()
        time_stamps, datapoints = data_convert_helper(request_count)
        return jsonify({
            'isSuccess': True,
            'timestamps': time_stamps,
            'datapoints': datapoints
        })
    except botocore.exceptions.ClientError as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/host_count', methods=['GET'])
def get_worker_pool_size():
    try:
        host_count = manager.ec2_manager.get_elb_healthy_host_count()
        time_stamps, datapoints = data_convert_helper(host_count)
        return jsonify({
            'isSuccess': True,
            'sizes': datapoints,
            'timestamps': time_stamps
        })
    except botocore.exceptions.ClientError as e:
        print(e)
        return jsonify({
            'isSuccess': False,
            'message': e.args
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
