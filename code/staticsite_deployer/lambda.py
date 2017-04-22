from __future__ import print_function

import zipfile
from subprocess import Popen, PIPE
import tempfile
import traceback

import boto3
from boto3.session import Session
import botocore


cf = boto3.client('cloudformation')
code_pipeline = boto3.client('codepipeline')


def extract_artifact(s3, artifact):
    bucket = artifact['location']['s3Location']['bucketName']
    key = artifact['location']['s3Location']['objectKey']
    import uuid
    rand_uuid = str(uuid.uuid4())
    temp_dir = '/tmp/%s/' % rand_uuid
    print('Temp dir name %s' % temp_dir)
    with tempfile.NamedTemporaryFile() as tmp_file:
        s3.download_file(bucket, key, tmp_file.name)
        with zipfile.ZipFile(tmp_file.name, 'r') as zip:
            zip.extractall(temp_dir)
    return temp_dir


def put_job_success(job, message):
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)


def put_job_failure(job, message):
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job,
                                         failureDetails={'message': message,
                                                         'type': 'JobFailed'})


def setup_s3_client(job_data):
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']

    session = Session(aws_access_key_id=key_id,
                      aws_secret_access_key=key_secret,
                      aws_session_token=session_token)
    return session.client('s3', config=botocore.client.Config(signature_version='s3v4'))


def upload_to_s3(client, path, target_bucket):
    task = ['/usr/bin/python', 'aws.py',
            's3', 'sync', '--delete',
            path + '/_site', 's3://' + target_bucket + '/']
    p = Popen(task, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    message = '%s\n%s' % (stdout, stderr)
    print(message)


def lambda_handler(event, context):

    try:
        job_id = event['CodePipeline.job']['id']
        job_data = event['CodePipeline.job']['data']
        target_bucket = event['CodePipeline.job']['data'][
            'actionConfiguration']['configuration']['UserParameters']
        artifact = job_data['inputArtifacts'][0]
        s3 = setup_s3_client(job_data)
        artifact_dir = extract_artifact(s3, artifact)
        upload_to_s3(s3, artifact_dir, target_bucket)
        put_job_success(job_id, 'Successfully uploaded artifact to %s' % target_bucket)

    except Exception as e:
        print('Function failed due to exception.')
        print(e)
        traceback.print_exc()
        put_job_failure(job_id, 'Function exception: ' + str(e))

    print('Function complete.')
    return "Complete."
