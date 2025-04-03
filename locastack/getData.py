import boto3

# Configure boto3 to use LocalStack endpoint
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',  # use the default access key
    aws_secret_access_key='test',  # use the default secret key
)

# Define the bucket name and object key
bucket_name = 'sample-bucket'
object_key = 'sales_data/part-00000-309aae73-1fee-4127-a603-a6f68d20ced4-c000.csv'

# Download the file from S3 bucket
response = s3.get_object(Bucket=bucket_name, Key=object_key)
data = response['Body'].read()

print(f"File '{object_key}' downloaded from s3://{bucket_name}/ whose values is {data}")
