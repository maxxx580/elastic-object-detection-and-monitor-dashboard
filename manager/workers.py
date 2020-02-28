from flask import Blueprint, jsonify, request
from manager.aws import instance_manager
import manager

bp = Blueprint("workers", __name__, url_prefix='/workers')
ec2_manager = instance_manager.InstanceManager()


@bp.route('/cpu', methods=['GET'])
def get_worker_cpu_usage():

    try:
        cpu_usage_data = ec2_manager.get_cpu_utilization()
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
        inbound_traffic = ec2_manager.get_instance_inbound_rate()
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


@bp.route('/pool_size', methods=['GET'])
def get_worker_pool_size():
    return jsonify({'size': len(manager.worker_pool_size)})


@bp.route('/', methods=['GET', 'POST', 'DELETE'])
def workers():
    try:
        if request.methods == 'GET':
            instances = ec2_manager.get_instances()
            return jsonify({
                'isSuccess': True,
                'data': instances
            })

    except Exception as e:
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


def data_convert_helper(response):
    time_stamps = [datapoint[0] for datapoint in response]
    datapoints = [datapoint[1] for datapoint in response]
    return [time_stamps, datapoints]
