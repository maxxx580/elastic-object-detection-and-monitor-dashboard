import threading


class AutoScaler():

    def __init__(self, ec2_manager):
        self.worker_pool = set()
        self.starting_up_pool = set()
        self.shunting_down_pool = set()
        self.ec2_manager = ec2_manager
        self.pool_lock = threading.Lock()

    def auto_scale(self): #2 MINUTES
        # TODO: check CPU utilization for last 2 minutes / every 2 minutes,

        pass

    def scale_up(self, k=1):
        instances = self.ec2_manager.launch_instance(k)
        self.pool_lock.acquire()
        for instance in instances:
            self.starting_up_pool.add(instance['InstanceId'])
        self.pool_lock.release()
        return instances

    def scale_down(self, k=1):
        assert len(self.worker_pool) > k, 'k is more than number of instances'
        instances_to_terminated = set()
        for i in range(k):
            instances_to_terminated.add(list(self.worker_pool)[i])
        self.pool_lock.acquire()
        for instance in list(self.worker_pool):
            if instance in instances_to_terminated:
                self.worker_pool.remove(instance)
                self.shunting_down_pool.add(instance)
        self.pool_lock.release()

    def auto_update(self): #30 SECONDS
        if self.shunting_down_pool:
            instances_terminated = self.ec2_manager.terminate_instance(
                list(self.shunting_down_pool))
            self.pool_lock.acquire()
            self.shunting_down_pool.difference_update(
                set(instances_terminated))
            self.pool_lock.release
            # TODO: de-register them to ELB
            self.ec2_manager.unregister_instances_elb(self, instances_terminated)

        if len(self.starting_up_pool) > 0:
            instances_deployed = list(filter(
                lambda x: x['state']['Name'] == 'running', self.ec2_manager.get_instance_status(list(self.starting_up_pool))))

            deployed_instances_id = {instance['id']
                                     for instance in instances_deployed}
            self.pool_lock.acquire()
            for iid in deployed_instances_id:
                self.worker_pool.add(iid)
                self.starting_up_pool.remove(iid+'')
            self.pool_lock.release()
            # TODO: register them to ELB
            self.ec2_manager.register_instances_elb(self, deployed_instances_id)

