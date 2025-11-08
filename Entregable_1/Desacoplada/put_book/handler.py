import json
import boto3
import os
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError

def convert_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, list):
        return [convert_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    else:
        return obj

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = os.getenv('DB_DYNAMONAME', 'BooksLambdaTable')
    table = dynamodb.Table(table_name)
    
    try:
        # Obtener book_id de los path parameters
        book_id = event.get('pathParameters', {}).get('book_id')
        
        if not book_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'book_id is required'})
            }
        
        # Verificar que el libro existe
        existing = table.get_item(Key={'book_id': book_id})
        if 'Item' not in existing:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Book not found'})
            }
        
        # Parsear el body
        body = json.loads(event.get('body', '{}'))
        
        # Actualizar timestamp y mantener book_id
        body['book_id'] = book_id
        body['updated_at'] = datetime.utcnow().isoformat()
        
        # Mantener created_at si existe
        if 'created_at' in existing['Item']:
            body['created_at'] = existing['Item']['created_at']
        
        # Convertir floats a Decimal
        item_dict = convert_to_decimal(body)
        
        # Actualizar en DynamoDB
        table.put_item(Item=item_dict)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Book updated successfully',
                'book_id': book_id
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
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