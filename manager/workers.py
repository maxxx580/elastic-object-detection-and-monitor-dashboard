from flask import Blueprint, jsonify
from manager.aws import instance_manager

bp = Blueprint("workers", __name__, url_prefix='/workers')
manager = instance_manager.InstanceManager()


@bp.route('/cpu', methods=['GET'])
def get_worker_cpu_useage():

    try:
        cpu_usage_data = manager.get_cpu_utilization()
        time_stamps, datapoints = data_convert_helper(cpu_usage_data)
        return jsonify({
            'isSuccess': True,
            'timestamps': time_stamps,
            'datapoints': datapoints
        })
    except Exception as e:
        print(e)
        return jsonify({
            'isSuccess': False
        })


@bp.route('/traffic', methods=['GET'])
def get_worker_inbount_traffic():
    try:
        inbound_traffic = manager.get_instance_inbound_rate()
        time_stamps, datapoints = data_convert_helper(inbound_traffic)
        return jsonify({
            'isSuccess': True,
            'timestamps': time_stamps,
            'datapoints': datapoints
        })
    except Exception as e:
        print(e)
        return jsonify({
            'isSuccess': False
        })


@bp.route('/', methods=['GET', 'POST', 'DELETE'])
def configure_workers():
    pass


def data_convert_helper(response):
    time_stamps = [datapoint[0] for datapoint in response]
    datapoints = [datapoint[1] for datapoint in response]
    return [time_stamps, datapoints]
