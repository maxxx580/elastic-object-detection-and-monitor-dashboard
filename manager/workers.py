import logging

import botocore
from flask import Blueprint, abort, jsonify, request

import manager
from manager.aws import autoscale, instance_manager

bp = Blueprint("workers", __name__, url_prefix='/workers')
logger = logging.getLogger('manager')


@bp.route('/cpu', methods=['GET'])
def get_worker_cpu_usage():
    """[summary] this endpoint retrieves the average CPU user per minute for the past 30 minutes.

    Returns:
        [type] -- [description] this endpoins return a json object
        {
            isSuccess: boolean indecating if the action is successful,
            timestamps: list of timestamps for each datapoint ,
            datapoints: list of average cpu usage per minute,
            message: error mssage if applicable
        }
    """
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
    """[summary] this endpoint retrieves the sum of number of requests per minute for the past 30 minutes. 

    Returns:
        [type] -- [description] this endpoint returns an json object
        {
            isSuccess: boolean indecating if the action is successful,
            timestamps: list of timestamps for each datapoint ,
            datapoints: list of sum of number of requests per minute,
            message: error mssage if applicable
        }
    """
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
    """[summary] this endpoint retrieves the maximum number of targets per minute registered to the elastic load balancer. 

    Returns:
        [type] -- [description] this method returns a json object. 
        {
            isSuccess: boolean indecating if the action is successful,
            timestamps: list of timestamps for each datapoint ,
            datapoints: list of maximum number of healthy hosts per minute,
            message: error mssage if applicable
        }
    """
    try:
        host_count = manager.ec2_manager.get_elb_healthy_host_count()
        time_stamps, datapoints = data_convert_helper(host_count)
        return jsonify({
            'isSuccess': True,
            'datapoints': datapoints,
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
    """[summary] This endpoint performs three kinds of action based on the HTTP methods. 
    Given a GET request, it retrieves a list of instances in pending, running, and shutting-down states.
    Given a POST request, it scale up the worker pool by one. 
    Given a DELETE request, it scale down the worker pool by one. 

    Returns:
        [type] -- [description] this method returns a json object. 
        {
            isSuccess: boolean indecating if the action is successful,
            data: list of instances created if applicable
            message: error mssage if applicable if applicable
        }
    """
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
