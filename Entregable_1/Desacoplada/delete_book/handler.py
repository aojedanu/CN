import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = os.getenv('DB_DYNAMONAME', 'books-table')
    table = dynamodb.Table(table_name)
    
    try:
        # Obtener book_id de los path parameters
        book_id = event.get('pathParameters', {}).get('book_id')
        
        if not book_id:
            return {
                'statusCode': 400,
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
                'body': json.dumps({'error': 'Book not found'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Book deleted successfully',
                'book_id': book_id
            })
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }