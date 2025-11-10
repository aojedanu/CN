from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
import psycopg2
from botocore.exceptions import ClientError
from models.book import Book
from db.dynamodb_db import DynamoDBDatabase




app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials= True) # permite cabeceras de autenticacion de otras entidades

try:
    db = DynamoDBDatabase() 
except ValueError as e:
    raise RuntimeError(f"Error initializing DB: {e}") from e


@app.route('/books', methods=['POST'])
def create_item():
    try:
        data = request.get_json()
        book = Book(**data)
        created = db.create_book(book)
        return jsonify(created.model_dump()), 201
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.IntegrityError as e:
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 409
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = db.get_book(book_id)
        if book:
            return jsonify(book.model_dump()), 200
        return jsonify({'error': 'Item no encontrado'}), 404
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

@app.route('/books', methods=['GET'])
def get_all_books():
    try:
        books = db.get_all_books()
        return jsonify([t.model_dump() for t in books]), 200
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

@app.route('/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    try:
        data = request.get_json()
        data.pop('book_id', None)
        data.pop('created_at', None)
        book = Book(**data)
        updated = db.update_book(book_id, book)
        if updated:
            return jsonify(updated.model_dump()), 200
        return jsonify({'error': 'Item no encontrado'}), 404
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except psycopg2.IntegrityError as e:
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 409
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        if db.delete_book(book_id):
            return '', 204
        return jsonify({'error': 'book no encontrado'}), 404
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)