import time
from datetime import datetime, timedelta
from operator import itemgetter

import boto3


class InstanceManager:

    def __init__(self):

        self.cw = boto3.client('cloudwatch')
        self.ec2 = boto3.client('ec2')
        self.elb = boto3.client('elbv2')

        self.user_app_tag = 'ece1779-a2-worker'
        self.image_id = 'ami-0c1d9d416e381c787'
        self.instance_type = 't2.small'
        self.key_pair = 'keypair'
        # rachel's elb
        self.TargetGroupArn = 'arn:aws:elasticloadbalancing:us-east-1:992704428121:targetgroup/ece1779-a2-target-group/0feaa7080487b1c6'
        # eric's elb
        self.TargetGroupArn = 'arn:aws:elasticloadbalancing:us-east-1:728815168568:targetgroup/worker/f7269e70cd56ae73'
        self.security_group = ['launch-wizard-1']
        self.tag_specification = [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': self.user_app_tag
                }]
        }]
        self.monitoring = {'Enabled': True}
        self.tag_placement = {'AvailabilityZone': 'us-east-1c'}
        self.iam_profile = {
            'Arn': 'arn:aws:iam::728815168568:instance-profile/ece1779-a2',
            'Name': 'ece1779-a2'
        }
        self.elb_profile = {
            'Name': 'LoadBalancer',
            'Value': 'app/ece1779/ad995928e73f7eb9'
        }
        self.elb_target_profile = {
            'Name': 'TargetGroup',
            'Value': 'targetgroup/worker/f7269e70cd56ae73'
        }

    def launch_instances(self, k=1):
        print("********* ec2 manager launching instances *****************")
        response = self.ec2.run_instances(ImageId=self.image_id,
                                          InstanceType=self.instance_type,
                                          KeyName=self.key_pair,
                                          MinCount=1,
                                          MaxCount=k,
                                          SecurityGroups=self.security_group,
                                          TagSpecifications=self.tag_specification,
                                          Monitoring=self.monitoring,
                                          Placement=self.tag_placement)
        return response['Instances']

    def attach_instances_to_IAM_role(self, instance_ids):
        for instance_id in instance_ids:
            self.ec2.associate_iam_instance_profile(
                IamInstanceProfile=self.iam_profile,
                InstanceId=instance_id
            )

    def terminate_instances(self, instance_ids):
        print("********* ec2 manager terminate instances *****************")
        assert all(isinstance(instance_id, str)
                   for instance_id in instance_ids)

        self.ec2.terminate_instances(InstanceIds=instance_ids, DryRun=False)
        return instance_ids

    def get_instance_status(self, instance_ids):
        response = self.ec2.describe_instance_status(InstanceIds=instance_ids)
        return [{"id": instance_status['InstanceId'], "state":instance_status['InstanceState']}
                for instance_status in response['InstanceStatuses']]

    def get_instances(self, live_only=False):
        worker_instance_filter = {
            'Name': 'tag:' + 'Name',
            'Values': [self.user_app_tag]
        }
        response = self.ec2.describe_instances(
            Filters=[worker_instance_filter])
        response_restructured = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                response_restructured.append(instance)

        if live_only:
            response_restructured = list(filter(lambda x: x['State']['Name'] in ['pending', 'running', 'shutting-down'],
                                                response_restructured))
        return response_restructured

    def get_cpu_utilization(self, k=30):
        statistics = 'Average'
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=k * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Unit='Percent',
            Statistics=[statistics]
        )
        return self._data_conversion_helper(response, statistics)

    def get_elb_request_count(self):
        statistics = 'Sum'
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName='RequestCount',
            Namespace='AWS/ApplicationELB',
            Statistics=[statistics],
            Dimensions=[self.elb_profile, self.elb_target_profile]
        )
        return self._data_conversion_helper(response, statistics)

    def get_elb_healthy_host_count(self):
        statistics = 'Average'
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName='HealthyHostCount',
            Namespace='AWS/ApplicationELB',
            Statistics=[statistics],
            Dimensions=[self.elb_profile, self.elb_target_profile]
        )
        return self._data_conversion_helper(response, statistics)

    def register_instances_elb(self, instance_ids):
        print("***********              registering instances          **************")
        print(instance_ids)
        response = self.elb.register_targets(
            TargetGroupArn=self.TargetGroupArn,
            Targets=[
                {
                    'Id': instance_id,
                    'Port': 5000
                }
                for instance_id in list(instance_ids)
            ]
        )
        return response

    def unregister_instances_elb(self, instance_ids):
        print("***********              deregistering instances          **************")
        print(instance_ids)
        response = self.elb.deregister_targets(
            TargetGroupArn=self.TargetGroupArn,
            Targets=[
                {
                    'Id': instance_id,
                    'Port': 5000
                }
                for instance_id in list(instance_ids)
            ]
        )
        return response

    def _data_conversion_helper(self, response, statistics):
        res = [[point['Timestamp'].hour+point['Timestamp'].minute/60,
                point[statistics]] for point in response['Datapoints']]
        return sorted(res, key=itemgetter(0))


if __name__ == "__main__":
    manager = InstanceManager()
