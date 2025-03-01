import json
import base64
import boto3
import os
import uuid
import botocore
import imghdr
import requests

s3 = boto3.client('s3')

# one day in seconds
EXPIRES_IN_SECONDS = 60*60*24

def stream_to_s3(url, key):
    s3_bucket = os.environ['bucket']
    session = requests.Session()
    response = session.get(url, stream=True)
    # TODO look for Content-Disposition header, which might have file name:
    # Content-Disposition: ...; filename="foo.txt"
    # If so, use it in the saved file
    with response as part:
        # TODO enforce size limit
        part.raw.decode_content = True
        conf = boto3.s3.transfer.TransferConfig(multipart_threshold=10000, max_concurrency=4)
        s3.upload_fileobj(part.raw, s3_bucket, key, Config=conf)
    response = s3.generate_presigned_url('get_object',
        Params={'Bucket': s3_bucket,'Key': key}, ExpiresIn=EXPIRES_IN_SECONDS)
    return response

def handler(event, context):
    print(event)
    # Generate random image id
    key = str(uuid.uuid4())

    data = json.loads(event['body'])
    url = data['url']

    try:
        url = stream_to_s3(url, key)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*.synapse.org'
            },
            'body': json.dumps({'url',url})
        }
    except:
        return {
            'statusCode': 500,
            'body': json.dumps('Request Failed!') # TODO include error message
        }
