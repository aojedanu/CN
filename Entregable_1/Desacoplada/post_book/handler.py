import json
import boto3
import os
from decimal import Decimal
from datetime import datetime
import uuid
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
    table_name = os.getenv('DB_DYNAMONAME', 'books-table')
    table = dynamodb.Table(table_name)
    
    try:
        # Parsear el body
        body = json.loads(event.get('body', '{}'))
        
        # Validar que tenga al menos 3 atributos válidos
        non_empty_fields = {
            k: v for k, v in body.items()
            if v not in (None, "", [], {}) and k not in ("book_id", "created_at", "updated_at")
        }
        
        if len(non_empty_fields) < 3:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El libro debe tener al menos 3 atributos con valor.'
                })
            }
        
        # Generar ID y timestamps
        book_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        body['book_id'] = book_id
        body['created_at'] = timestamp
        body['updated_at'] = timestamp
        
        # Convertir floats a Decimal para DynamoDB
        item_dict = convert_to_decimal(body)
        
        # Guardar en DynamoDB
        table.put_item(Item=item_dict)
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Book created successfully',
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