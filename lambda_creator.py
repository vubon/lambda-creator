"""
Licensed under MIT.
@since: 2020

It will
    - Create a new lambda function
        - Add lambda permission
        - Add lambda variables
        - Add lambda layers
        - Add lambda trigger event (Currently only S3 bucket trigger)

    - Update existing lambda function codebase
"""
__version__ = "0.0.1"
__author__ = "Vubon Roy"

import json
import uuid

import boto3

aws_lambda = boto3.client('lambda')
s3 = boto3.resource('s3')


def function_creator(**kwargs: dict) -> dict:
    """
    Description: This function will create a new lambda function.
    :type kwargs: dict
    :param kwargs: function details
    :return: lambda function details
        - example:
        {
          "ResponseMetadata": {
            "RequestId": "0b90502f-44ae-48ca-9d39-b2e808ea53a8",
            "HTTPStatusCode": 201,
            "HTTPHeaders": {
              "date": "Thu, 30 Jan 2020 11:34:04 GMT",
              "content-type": "application/json",
              "content-length": "1009",
              "connection": "keep-alive",
              "x-amzn-requestid": "0b90502f-44ae-48ca-9d39-b2e808ea53a8"
            },
            "RetryAttempts": 0
          },
          "FunctionName": "helloworld",
          "FunctionArn": "arn:aws:lambda:us-east-1:<AccountID>:function:helloworld",
          "Runtime": "python3.8",
          "Role": "arn:aws:iam::<AccountID>:role/lambda-function-role",
          "Handler": "lambda_function.lambda_handler",
          "CodeSize": 339,
          "Description": "This is testing function for automation deploy in lambda",
          "Timeout": 300,
          "MemorySize": 128,
          "LastModified": "2020-01-30T11:34:02.619+0000",
          "CodeSha256": "GZitKzniISPkoIMyRWf7ss/kHtm/KcddtdTdrSxZxwI=",
          "Version": "1",
          "Environment": {
            "Variables": {
              "password": "password",
              "host": "RDS",
              "username": "username"
            }
          },
          "TracingConfig": {
            "Mode": "PassThrough"
          },
          "RevisionId": "f142cdcd-d5be-42ff-89d3-a611a77fc85d",
          "Layers": [
            {
              "Arn": "arn:aws:lambda:us-east-1:<AccountID>:layer:test_layer:2",
              "CodeSize": 1013
            }
          ],
          "State": "Active",
          "LastUpdateStatus": "Successful"
        }
    :rtype: dict
    """
    response = aws_lambda.create_function(**kwargs)
    # This response store in cloud watch
    print(f"New function is created {response}")
    return response


def lambda_add_permission(bucket_name: str, fn_name: str) -> None:
    """
    Description: Basically, this will handle lambda permission. Currently we just handle s3 invoke.
    Maybe in the future would add more permissions for other services.
    :type bucket_name: str
    :param bucket_name: S3 bucket name : example-bucket
    :type fn_name: str
    :param fn_name: Lambda function name . example : example-function
    :return: None
    """
    aws_lambda.add_permission(
        FunctionName=fn_name,
        StatementId=f"{uuid.uuid4()}",
        Action='lambda:InvokeFunction',
        Principal='s3.amazonaws.com',
        SourceArn=f'arn:aws:s3:::{bucket_name}',
    )


def add_s3_event_trigger(notification: dict, bucket_name: str) -> None:
    """
    Description: This function will handle S3 notification event trigger with lambda function.
    :type notification: dict
    :param notification: Notification payload data. where notification conditions will exists. Such as create, update
                        etc and also filter conditions such as suffix and prefix filter.
    :type bucket_name: str
    :param bucket_name: bucket name which generate notification for lambda
    :return: Nothing
    :rtype: None
    Example notification payload sample:
        {
          "LambdaFunctionArn": "arn:aws:lambda:us-east-1:<AccountID>:function:test",
          "Events": [
            "s3:ObjectCreated:*"
          ],
          "Filter": {
            "Key": {
              "FilterRules": [
                {
                  "Name": "suffix",
                  "Value": ".jpg"
                }
              ]
            }
          }
        }
    """
    bucket = s3.BucketNotification(bucket_name)
    event = {
        "NotificationConfiguration": {
            'LambdaFunctionConfigurations': [notification]
        }
    }
    # put notification trigger in s3 bucket
    bucket.put(**event)


def lambda_creator_decider(details: dict) -> None:
    """
    Description: This function will decide few things such as create variables, notification and layers

    :raises
        - If function name invalid.
        - If variables data invalid.
        - If notification payload invalid.
        - If layer data invalid.
        - If runtime name invalid

    :type details: dict
    :param details: new function create details. SUch as function name, Function Role etc.
        Example:
            {
              "FunctionName": "helloworld",
              "Version": "1.0.0",
              "Role": "arn:aws:iam::<AccountID>:role/lambda-function-role",
              "Details": "This is testing function for automation deploy in lambda",
              "Timeout": 300,
              "MemorySize": 128,
              "Runtime": "python3.8",
              "Publish": true,
              "Layers": [
                "arn:aws:lambda:us-east-1:<AccountID>:layer:test_layer:2"
              ],
              "Variables": {
                  "host": "RDS",
                  "username": "username",
                  "password": "password"
              },
              "Notification": {
                "BucketName": "test-vubon",
                "Action": {
                  "Events": [
                    "s3:ObjectCreated:*"
                  ],
                  "Filter": {
                    "Key": {
                      "FilterRules": [
                        {
                          "Name": "suffix",
                          "Value": ".jpg"
                        }
                      ]
                    }
                  }
                }
              }
            }
    :return: None
    :rtype: None
    """
    try:

        common_data = dict(
            FunctionName=details.get("FunctionName", "default-function"),
            Runtime=details.get('Runtime', 'python3.8'),
            Role=details.get("Role", "< Lambda Role >"),
            Handler='lambda_function.lambda_handler',
            Code={
                'S3Bucket': details.get("bucket_name"),
                'S3Key': details.get("key")
            },
            Description=details.get("Details", "default details"),
            Timeout=details.get("Timeout", 500),
            MemorySize=details.get("MemorySize", 300),
            Publish=details.get("Publish", False),
        )
        # If set layers on the function
        layers = details.get("Layers")
        if layers:
            common_data.update({"Layers": layers})

        # If set variable on the function
        variables = details.get("Variables")
        if variables:
            common_data.update({"Environment": {"Variables": variables}})

        # If has VPC Configuration
        vpc_config = details.get("VpcConfig")
        if vpc_config:
            common_data.update({"VpcConfig": vpc_config})

        # create new lambda
        response = function_creator(**common_data)

        notification = details.get("Notification")
        if notification:
            # Giving S3 invoke permission the function
            lambda_add_permission(bucket_name=notification.get("BucketName"), fn_name=response.get("FunctionName"))

            # add s3 bucket trigger with create function
            action = notification.get("Action")
            action.update({"LambdaFunctionArn": response.get("FunctionArn")})
            add_s3_event_trigger(bucket_name=notification.get("BucketName"), notification=action)

    except Exception as err:
        print(err)


def lambda_updater(details: dict, current_fn_res: dict) -> None:
    """
    This function will update current codebase of a lambda function and instantly publish the new version of the lambda

    :raises
        - If any information will miss from details. The function won't update and raise error. You could check the
          error from cloud watch service.

    :type details: dict
    :param details: lambda function details. Such as function name and bucket name , bucket object key etc.
        example -
            {
                "FunctionName": "Update lambda function name"
                "bucket_name": "bucket name",
                "key": "bucket object key, such as lambda.zip"
            }
        [N.B. If from details do not get function name, then get function name from current function response data]

    :type current_fn_res: dict
    :param current_fn_res:
            Fetch lambda function details. Where we can find all information of the lambda function. If somehow miss the
            function details in details param. then we can get the function name from current_fn_res data.
    :return: None
    :rtype: None

    Update response look like below data
    {
      "ResponseMetadata": {
        "RequestId": "81d6956e-30ef-413f-a543-8b3c2f708980",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
          "date": "Thu, 30 Jan 2020 11:21:21 GMT",
          "content-type": "application/json",
          "content-length": "924",
          "connection": "keep-alive",
          "x-amzn-requestid": "81d6956e-30ef-413f-a543-8b3c2f708980"
        },
        "RetryAttempts": 0
      },
      "FunctionName": "example",
      "FunctionArn": "arn:aws:lambda:us-east-1:<AccountID>:function:example:2",
      "Runtime": "python3.8",
      "Role": "arn:aws:iam::< AccountID >:role/lambda-function-role",
      "Handler": "lambda_function.lambda_handler",
      "CodeSize": 339,
      "Description": "This is testing function for automation deploy in lambda",
      "Timeout": 300,
      "MemorySize": 128,
      "LastModified": "2020-01-30T11:21:21.253+0000",
      "CodeSha256": "b61itErhtXvIR2HEvqHNMYVTyOJS85j8ufE6Cw7z3zI=",
      "Version": "2",
      "TracingConfig": {
        "Mode": "PassThrough"
      },
      "RevisionId": "e44775d3-4f3e-4424-a651-0ec16e37724a",
      "Layers": [
        {
          "Arn": "arn:aws:lambda:us-east-1:<AccountID>:layer:test_layer:2",
          "CodeSize": 1013
        }
      ],
      "State": "Active",
      "LastUpdateStatus": "Successful"
    }
    """
    update = aws_lambda.update_function_code(
        FunctionName=details.get("FunctionName", current_fn_res.get("Configuration").get("FunctionName")),
        S3Bucket=details.get("bucket_name"),
        S3Key=details.get("key"),
        Publish=True
    )
    # update data store in cloud watch log service
    print(f"Function is updated {update}")


def lambda_handler(event, context) -> None:
    """
    Description: This is the main function of the lambda function.
    :type: dict
    :param event: AWS Lambda uses this parameter to pass in event data to the handler. This parameter is usually of the
                  Python dict type. It can also be list, str, int, float, or NoneType type.When you invoke your
                  function, you determine the content and structure of the event. When an AWS service invokes your
                  function, the event structure varies by service. For details, see
                  - https://docs.aws.amazon.com/lambda/latest/dg/lambda-services.html
    :param context: AWS Lambda uses this parameter to provide runtime information to your handler. For details
        - https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    :return: None
    :rtype: None
    """
    # Get bucket name and key name from event notification
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    # Get function.json file from the bucket
    obj = s3.Object(bucket_name, "function.json")
    body = obj.get()['Body'].read()

    # convert as dict
    lambda_details = json.loads(body)
    # update lambda details with bucket name and key value
    lambda_details.update({"bucket_name": bucket_name, "key": key})

    try:
        # checking function exist or not .
        response = aws_lambda.get_function(FunctionName=lambda_details.get("FunctionName", ""))
        # update lambda function
        lambda_updater(details=lambda_details, current_fn_res=response)
    except Exception as err:
        print(err)
        # call function_creator function
        lambda_creator_decider(details=lambda_details)
