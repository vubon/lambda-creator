import json


def lambda_handler(event, context):
    print("All features test")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
