import boto3
import time

from datetime import datetime, timedelta
from operator import itemgetter


class InstanceManager:

    def __init__(self):

        self.cw = boto3.client('cloudwatch')
        self.ec2 = boto3.client('ec2')
        self.ssm = boto3.client('ssm')

        self.user_app_tag = 'ece1779-a2'
        self.image_id = 'ami-baf632ac'
        self.instance_type = 't2.small'
        self.key_pair = 'ece1779'
        self.security_group = ['launch-wizard-2']
        self.tag_specification = [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': self.user_app_tag
                }]
        }]
        self.monitoring = {'Enabled': True}
        self.tag_placement = {'AvailabilityZone': 'us-east-1a'}

    def launch_instance(self, k=1):
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

    def terminate_instance(self, instance_id):
        assert all(isinstance(instance_id, str)
                   for instance_id in instance_id)
        self.ec2.terminate_instances(InstanceIds=[instance_id], DryRun=False)
        return instance_id

    def get_instance_status(self, instance_id):
        response = self.ec2.describe_instance_status(InstanceIds=[instance_id])
        return [{"id": instance_status['InstanceId'], "state":instance_status['InstanceState']}
                for instance_status in response['InstanceStatuses']]

    def get_instances(self):
        response = self.ec2.describe_instances()
        return response['Reservations']

    def deploy_instance(self, instance_ids):
        # TODO: use aws code deploy
        pass

    def get_cup_utilization(self, instance_ids):
        response = self.cw.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}
                        for instance_id in instance_ids],
            StartTime=datetime.utcnow() - timedelta(seconds=60 * 2),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            Period=1 * 60,
            Statistics=[
                'Average',
            ],
            Unit='Percent'
        )

        cpu_stats = []
        for point in response['Datapoints']:
            hour = point['Timestamp'].hour
            minute = point['Timestamp'].minute
            time = hour + minute/60
            cpu_stats.append([time, point['Average']])

        cpu_stats = sorted(cpu_stats, key=itemgetter(0))

        return cpu_stats

    def get_instance_inbound_rate(self, instance_ids):
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=1 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}
                        for instance_id in instance_ids],
            MetricName='NetworkIn',
            Namespace='AWS/EC2',  # Unit='Percent',
            Statistics=['Sum']
        )

        return response


if __name__ == "__main__":
    manager = InstanceManager()
    instances = manager.get_instances()
    # print(instances)
    print("instance id is " + str(instances[0]['Instances'][0]['InstanceId']))
    cpu_usage = manager.get_cup_utilization(
        [instances[0]['Instances'][0]['InstanceId']])
    # print(cpu_usage)
