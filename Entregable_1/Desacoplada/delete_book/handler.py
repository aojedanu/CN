import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Headers CORS
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
        
        # Eliminar el libro
        response = table.delete_item(
            Key={'book_id': book_id},
            ReturnValues='ALL_OLD'
        )
        
        if 'Attributes' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Book not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'message': 'Book deleted successfully',
                'book_id': book_id
            })
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