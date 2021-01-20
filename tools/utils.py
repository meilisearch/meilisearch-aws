import datetime
import requests
import time
import boto3

STATUS_OK=0
STATUS_TIMEOUT=1
STATUS_ERROR=2

def wait_for_instance_running(instance, timeout_seconds=None):
    ec2 = boto3.resource('ec2')
    start_time = datetime.datetime.now()
    while True:
        if timeout_seconds is not None:
            if check_timeout(start_time, timeout_seconds) is STATUS_TIMEOUT:
                return STATUS_TIMEOUT, None
        instance = ec2.Instance(instance.id)
        if instance.state['Name'] != 'pending':
            if instance.state['Name'] == 'running':
                return STATUS_OK, instance.state['Name']
            return STATUS_ERROR, instance.state['Name']
        time.sleep(1)

def wait_for_health_check(instance, timeout_seconds=None):
    start_time = datetime.datetime.now()
    while True:
        if timeout_seconds is not None:
            if check_timeout(start_time, timeout_seconds) is STATUS_TIMEOUT:
                return STATUS_TIMEOUT 
        try:
            resp = requests.get("http://{}/health".format(instance.public_ip_address))
            if resp.status_code >=200 and resp.status_code < 300:
                return STATUS_OK
        except Exception as e:
                pass
        time.sleep(1)

def terminate_instance_and_exit(instance):
    print("   Terminating instance {}".format(instance.id))
    instance.terminate()
    print("EXITING PROGRAM WITH STATUS CODE 1")
    exit(1)

def check_timeout(start_time, timeout_seconds):
    elapsed_time = datetime.datetime.now() - start_time
    if elapsed_time.total_seconds() > timeout_seconds:
        return STATUS_TIMEOUT
    return STATUS_OK
