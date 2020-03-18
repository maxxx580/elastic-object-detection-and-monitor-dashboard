import boto3
from app.config import get_instanceId

try:
    # lock.acquire()
    with open('request.log') as f:
        for i, l in enumerate(f):
            pass
    # TODO: update aws custom metric here i+1 is the number of request in the past 1 min
    client = boto3.client('cloudwatch', region_name='us-east-1')
    instance_id = get_instanceId()
    instance_id = 'i-07ac7fe1685cda51c'
    print(instance_id)
    value = i + 1
    print(value)
    client.put_metric_data(
        MetricData=[{
            'MetricName': 'CountHTTPMetric',
            'Dimensions': [
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            'Unit': 'None',
            'Value': value
        },
        ],
        Namespace='CountHTTPNameSpace'
    )
except:
    pass
finally:
    open("request.log", "w").close()
    # lock.release()