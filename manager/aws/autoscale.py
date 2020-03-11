import atexit
import datetime
import math
import sys

import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
import manager
from manager.aws import autoscale, instance_manager
from random import random


class AutoScaler():
    """[summary]
        this class contains auto-scaling policy to provision worker instance pool.
    """

    def __init__(self, ec2_manager, upper_threshold, lower_threshold, increase_ratio, decrease_ratio):
        self.ec2_manager = ec2_manager
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.MAX_NUMBER_OF_INSTANCES = 10
        self.upper_threshold = 70
        self.lower_threshold = 30
        self.increase_ratio = 2
        self.decrease_ratio = 0.5
        atexit.register(lambda: self.scheduler.shutdown())

    def set_policy(self, upper_threshold, lower_threshold, increase_ratio, decrease_ratio):
        """[summary]

        Arguments:
            upper_threshold {[type]} -- [description]
            lower_threshold {[type]} -- [description]
            increase_ratio {[type]} -- [description]
            decrease_ratio {[type]} -- [description]
        """
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.increase_ratio = increase_ratio
        self.decrease_ratio = decrease_ratio

    def auto_scale(self):
        """[summary] this method should be involved periodically (every minute) to examine the average cpu usage for 
        the past 2 minutes. This method launches instances when the average cpu usage is above 70% and terminates instances
        when the average cpu is below 30%. The auto scaling policy targets 50% cpu usage and calculate the number 
        of instances needed based on this target. 
        """
        instances = self.ec2_manager.get_instances(alive=True)
        cpu_usage_data = self.ec2_manager.get_cpu_utilization(k=2)
        cpu_usage_data = [datapoint for _, datapoint in cpu_usage_data]
        cpu_avg = np.mean(cpu_usage_data)
        print("####################       CPU       #####################")
        print(cpu_avg)
        if cpu_avg >= self.upper_threshold:
            increase_pool = math.ceil(
                len(instances)*self.increase_ratio - len(instances))
            self.scale_up(k=increase_pool)
            print("####################    SCALE UP      #####################")
            print(increase_pool)
            print(self.increase_ratio)

        if cpu_avg <= self.lower_threshold:
            decrease_pool = int(
                len(instances) - len(instances)*self.decrease_ratio)
            self.scale_down(k=decrease_pool)
            print("####################    SCALE DOWN     #####################")
            print(decrease_pool)
            print(self.decrease_ratio)

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
        """[summary] this methods decreases the size of the worker instances pool. The minimum number of instances is 1.
        This method performs nothing when the minimum number of instances is reached.

        Keyword Arguments:
            k {int} -- [description] the number of instances to terminate(default: {1})
        """
        instances = self.ec2_manager.get_instances(alive=True)
        k = min(len(instances)-1, k)

        if k == 0:
            return
        instances_to_terminated = [instance['InstanceId']
                                   for instance in instances[:k]]

        self.ec2_manager.unregister_instances_elb(instances_to_terminated)
        self.ec2_manager.terminate_instances(instances_to_terminated)

    def _configure_instances(self, instance_ids):

        instances = self.ec2_manager.get_instance_status(instance_ids)

        pending_instances = filter(
            lambda instance: instance['state'] == 'pending', instances)
        running_instances = filter(
            lambda instance: instance['state'] == 'running', instances)

        if len(pending_instances) > 0:
            self.scheduler.add_job(
                func=lambda: self._configure_instances(
                    [instance['id'] for instance in pending_instances]),
                trigger='date',
                run_date=datetime.datetime.now() + datetime.timedelta(seconds=30))

        if len(running_instances) > 0:
            running_instance_ids = [instance['id']
                                    for instance in running_instances]
            self.ec2_manager.attach_instances_to_IAM_role(running_instance_ids)
            self.ec2_manager.register_instances_elb(running_instance_ids)
