import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from .db import Database
from models.book import Book
from decimal import Decimal
import os

class DynamoDBDatabase(Database):
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = os.getenv('DB_DYNAMONAME')
        self.table = self.dynamodb.Table(self.table_name)
        self.initialize()
    
    def initialize(self):
        try:
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # La tabla no existe, crearla
                print(f"Creando tabla DynamoDB '{self.table_name}'...")
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'book_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'book_id',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                # Esperar a que la tabla esté activa
                table.wait_until_exists()
                
                # Actualizar referencia a la tabla
                self.table = table
            else:
                raise
    
    #   def create_book(self, book: Book) -> Book:
    #       self.table.put_item(Item=book.model_dump())
    #       return book
    
   
    def create_book(self, book: Book) -> Book:
        # Convierte el modelo Pydantic a diccionario
        item_dict = book.model_dump()

        def convert_to_decimal(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, list):
                return [convert_to_decimal(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_decimal(v) for k, v in obj.items()}
            else:
                return obj

        item_dict = convert_to_decimal(item_dict)

        # Validar que tenga al menos 3 atributos válidos
        non_empty_fields = {
            k: v for k, v in item_dict.items()
            if v not in (None, "", [], {}) and k not in ("book_id", "created_at", "updated_at")
        }

        if len(non_empty_fields) < 3:
            raise ValueError("El libro debe tener al menos 3 atributos con valor.")

        # Guardar el item en DynamoDB
        self.table.put_item(Item=item_dict)
        return book
    
    def get_book(self, book_id: str) -> Optional[Book]:
        response = self.table.get_item(Key={'book_id': book_id})
        if 'Item' in response:
            return Book(**response['Item'])
        return None
    
    def get_all_books(self) -> List[Book]:
        response = self.table.scan()
        books = [Book(**item) for item in response.get('Items', [])]
        return sorted(books, key=lambda x: getattr(x, 'average_rating', 0))

    
    #def update_book(self, book_id: str, book: Book) -> Optional[Book]:
    #    book.update_timestamp()
    #    book.book_id = book_id
    #    self.table.update_item(Item=book.model_dump()) #antes habia un put mirar a ver si esto lo soluciona
    #    return book
    
    def update_book(self, book_id: str, book: Book) -> Optional[Book]:
        # Convertir el modelo a dict y eliminar campos vacíos o no actualizables
        updates = {
            k: v for k, v in book.model_dump().items()
            if v not in (None, "", [], {}) and k not in ("book_id", "created_at")
        }

        if not updates:
            raise ValueError("No hay campos válidos para actualizar.")

        # Convertir floats a Decimal para DynamoDB
        from decimal import Decimal
        for k, v in updates.items():
            if isinstance(v, float):
                updates[k] = Decimal(str(v))

        # Generar dinámicamente la expresión de actualización
        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates.keys())
        expr_attr_names = {f"#{k}": k for k in updates.keys()}
        expr_attr_values = {f":{k}": v for k, v in updates.items()}

        try:
            response = self.table.update_item(
                Key={"book_id": book_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW"  # Devuelve el nuevo estado del item
            )
            updated_item = response.get("Attributes")
            if updated_item:
                return Book(**updated_item)
            return None
        except ClientError as e:
            raise e



    def delete_book(self, book_id: str) -> bool:
        response = self.table.delete_item(
            Key={'book_id': book_id},
            ReturnValues='ALL_OLD'
        )
        return 'Attributes' in response