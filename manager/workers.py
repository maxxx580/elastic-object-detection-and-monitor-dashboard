from flask import Blueprint
from manager.aws import instance_manager

bp = Blueprint("workers", __name__, url_prefix='/workers')
manager = instance_manager.InstanceManager()


@bp.route('/cpu', methods=['GET'])
def get_worker_cpu_useage():
    try:
        instances = manager.get_instances()
    # cpu_usage_data = instance_manager.get_worker_cpu_useage()
        return 'get cpu usage'
    except:
        return "failed"


@bp.route('/traffic', methods=['GET'])
def get_worker_inbount_traffic():
    pass


@bp.route('/', methods=['GET', 'POST', 'DELETE'])
def configure_workers():
    pass
