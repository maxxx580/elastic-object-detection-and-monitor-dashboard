
class AutoScaler():

    def __init__(self, ec2_manager):
        print("###### auto scaller created #########")
        self.worker_pool = set()
        self.starting_up_pool = set()
        self.shunting_down_pool = set()
        self.ec2_manager = ec2_manager

    def autoscale(self):
        # TODO: 1.check if auto scale required. 2.deployed recently launched. 3. terminate shut down
        pass

    def scale_up(self):
        aws_instance = self.ec2_manager.launch_instance()

        # TODO: IMPORTANT !!!! this is for dev only. should add to starting up pool instead
        self.worker_pool.add(aws_instance[0]['InstanceId'])
        return aws_instance

    def scale_down(self, instance_id=None):
        print(self.worker_pool)
        assert len(self.worker_pool) >= 1, 'no instance left'

        if not instance_id:
            instance_id = list(self.worker_pool)[0]

        for instance in list(self.worker_pool):
            if instance == instance_id:
                self.worker_pool.remove(instance)
                self.shunting_down_pool.add(instance)
