import atexit
import datetime
import math
import sys

import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler

import manager
from manager.aws import autoscale, instance_manager


class AutoScaler():
    """[summary]
        this class contains auto-scaling policy to provision worker instance pool.
    """

    def __init__(self, ec2_manager):
        self.ec2_manager = ec2_manager
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.MAX_NUMBER_OF_INSTANCES = 10
        atexit.register(lambda: self.scheduler.shutdown())

    def auto_scale(self):
        """[summary] this method should be involved periodically (every minute) to examine the average cpu usage for 
        the past 2 minutes. This method luanches instances when the average cpu usage is above 70% and terminates instances 
        when the average cpu is below 30%. The auto scaling policy targets 50% cpu usage and calculate the number 
        of instances needed based on this target. 
        """
        instances = self.ec2_manager.get_instances(alive=True)
        cpu_usage_data = self.ec2_manager.get_cpu_utilization(k=2)
        cpu_avg = np.mean(cpu_usage_data)

        if cpu_avg >= 70:
            increase_pool = math.ceil(
                len(instances)*cpu_avg/50 - len(instances))
            self.scale_up(k=increase_pool)
            print("increase", increase_pool)

        if cpu_avg <= 30:
            decrease_pool = int(len(instances) - len(instances)*cpu_avg/50)
            self.scale_down(k=decrease_pool)
            print("decrease", decrease_pool)

    def scale_up(self, k=1):
        """[summary] this method increases the size of the worker instance pool. The maximum number of instances is 10. 
        This method performs nothing when the maximum number of instances is reached. 

        Keyword Arguments:
            k {int} -- [description] the number of instances to add. (default: {1})

        Returns:
            [type] -- a list of instance objects[description]
        """
        current_instances = self.ec2_manager.get_instances(alive=True)
        k = min(self.MAX_NUMBER_OF_INSTANCES - len(current_instances), k)

        if k == 0:
            return []

        instances = self.ec2_manager.launch_instances(k)
        instance_ids = [instance['InstanceId'] for instance in instances]

        self.scheduler.add_job(
            func=lambda: self._configure_instances(instance_ids),
            trigger='date',
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=120))

        return instances

    def scale_down(self, k=1):
        """[summary] this methods decreases the size of the worker instances pool. The mimimum number of instances is 1. 
        Thsi method performs nothing when the minimum number of instances is reached. 

        Keyword Arguments:
            k {int} -- [description] the number of instances to terminate(default: {1})
        """
        instances = self.ec2_manager.get_instances(alive=True)
        assert k < len(instances), 'k is more than number of instances'

        if k == 0:
            return
        instances_to_terminated = [instance['InstanceId']
                                   for instance in instances[:k]]

        self.ec2_manager.unregister_instances_elb(instances_to_terminated)
        self.ec2_manager.terminate_instances(instances_to_terminated)

    def _configure_instances(self, instance_ids):
        self.ec2_manager.attach_instances_to_IAM_role(instance_ids)
        self.ec2_manager.register_instances_elb(instance_ids)
