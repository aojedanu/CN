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
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = os.getenv('DB_DYNAMONAME', 'books-table')
    table = dynamodb.Table(table_name)
    
    try:
        # Obtener todos los libros
        response = table.scan()
        books = [decimal_to_float(item) for item in response.get('Items', [])]
        
        # Ordenar por average_rating (si existe)
        books_sorted = sorted(
            books, 
            key=lambda x: x.get('average_rating', 0), 
            reverse=True
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(books_sorted),
                'books': books_sorted
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