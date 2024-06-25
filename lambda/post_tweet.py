import json
import os
import boto3
import tweepy
import random
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Attr

# Hardcode the Twitter account name
TWITTER_ACCOUNT = 'nous'

# Initialize the SSM client
ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])

def get_ssm_parameter(param_name):
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return response['Parameter']['Value']

# Fetch configuration from SSM Parameter Store
SSM_PATH = f'/twitter/{TWITTER_ACCOUNT}'
consumer_key = get_ssm_parameter(f'{SSM_PATH}/consumer_key')
consumer_secret = get_ssm_parameter(f'{SSM_PATH}/consumer_secret')
access_token = get_ssm_parameter(f'{SSM_PATH}/access_token')
access_token_secret = get_ssm_parameter(f'{SSM_PATH}/access_token_secret')
bearer_token = get_ssm_parameter(f'{SSM_PATH}/bearer_token')
TABLE_NAME = get_ssm_parameter('/twitter/table_name')

# Create Twitter client
client = tweepy.Client(bearer_token=bearer_token, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def is_within_posting_hours():
    now_utc = datetime.now(timezone.utc)
    now_pst = now_utc - timedelta(hours=8)
    return 6 <= now_pst.hour < 24


def calculate_wait_time():
    wait_time = random.randint(60, 360) * 60
    now_utc = datetime.now(timezone.utc)
    now_pst = now_utc - timedelta(hours=8)
    next_run_time = now_pst + timedelta(seconds=wait_time)
    if 1 <= next_run_time.hour < 6:
        extra_wait = (6 - next_run_time.hour) * 60 * 60
        wait_time += extra_wait
    print(f"Calculated wait_time: {wait_time} seconds")
    return wait_time

def lambda_handler(event, context):
    if event.get('task') == 'calculate_wait_time':
        wait_time = calculate_wait_time()
        return {
            'statusCode': 200,
            'body': {
                'message': 'Wait time calculated.',
                'wait_time': wait_time,
                'continue': True
            }
        }
    
    wait_time = calculate_wait_time()
    if not is_within_posting_hours():
        return {
            'statusCode': 200,
            'body': {
                'message': 'Outside posting hours.',
                'wait_time': wait_time,
                'continue': False
            }
        }
    
    # Query for unposted tweets, sorted by ID (oldest first)
    response = table.scan(
        FilterExpression=Attr('posted').eq(False) & Attr('twitter_account').eq(TWITTER_ACCOUNT),
        ProjectionExpression='id, tweet',
        Select='SPECIFIC_ATTRIBUTES'
    )
    tweets = sorted(response['Items'], key=lambda x: x['id'])
    
    if not tweets:
        return {
            'statusCode': 200,
            'body': {
                'message': 'No tweets to post.',
                'wait_time': wait_time,
                'continue': False
            }
        }
    
    oldest_tweet = tweets[0]
    client.create_tweet(text=oldest_tweet['tweet'])
    table.update_item(
        Key={'id': oldest_tweet['id']},
        UpdateExpression='SET posted = :val1, #ts = :val2',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={
            ':val1': True,
            ':val2': str(datetime.now())
        }
    )
    
    return {
        'statusCode': 200,
        'body': {
            'message': 'Tweet posted successfully!',
            'wait_time': wait_time,
            'continue': True
        }
    }