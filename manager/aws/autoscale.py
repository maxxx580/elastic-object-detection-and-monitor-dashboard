
class AutoScaler():

    def __init__(self, ec2_manager):
        self.worker_pool = set()
        self.starting_up_pool = set()
        self.shunting_down_pool = set()
        self.ec2_manager = ec2_manager

    def auto_scale(self):
        pass

    def scale_up(self, k=1):
        instances = self.ec2_manager.launch_instance(k)
        for instance in instances:
            self.starting_up_pool.add(instance['InstanceId'])

        return instances

    def scale_down(self, instance_id=None):
        assert len(self.worker_pool) >= 1, 'no instance left'
        if not instance_id:
            instance_id = list(self.worker_pool)[0]
        for instance in list(self.worker_pool):
            if instance == instance_id:
                self.worker_pool.remove(instance)
                self.shunting_down_pool.add(instance)

    def auto_update(self):
        if self.shunting_down_pool:
            instances_to_terminate = list(filter(
                lambda x: x['state'] == 'terminated', self.ec2_manager.get_instance_status(list(self.shunting_down_pool))))
            instances_terminated = self.ec2_manager.terminate_instance(
                instances_to_terminate)
            self.shunting_down_pool -= set(instances_terminated)
            # TODO: de-register them to ELB

        if self.shunting_down_pool:
            instances_to_deploy = list(filter(
                lambda x: x['state'] == 'running', self.ec2_manager.get_instance_status(list(self.starting_up_pool))))
            instances_deployed = self.ec2_manager.deploy_instances(
                instances_to_deploy)
            self.starting_up_pool += set(instances_deployed)
            # TODO: register them to ELB
