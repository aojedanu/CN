import json
import boto3
import os
from decimal import Decimal
from botocore.exceptions import ClientError

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

def lambda_handler(event, context):
    # Headers CORS que se devolverán en TODAS las respuestas
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = os.getenv('DB_DYNAMONAME', 'books')
    table = dynamodb.Table(table_name)
    
    try:
        # Obtener id de los path parameters (CloudFormation usa 'id', no 'book_id')
        book_id = event.get('pathParameters', {}).get('id')
        
        if not book_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'book_id is required'})
            }
        
        # Obtener el libro
        response = table.get_item(Key={'book_id': book_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Book not found'})
            }
        
        book = decimal_to_float(response['Item'])
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(book)
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }