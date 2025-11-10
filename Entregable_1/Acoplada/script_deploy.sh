#!/bin/bash

REGION="us-east-1"
ECR_REPOSITORY_NAME="books-app"

if [ $# -ne 2 ]; then
    echo "Uso: $0 <VpcId> <SubnetIds (separadas por comas)>"
    exit 1
fi

VPC_ID=$1
SUBNET_IDS=$2


ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ]; then
    echo "Error obteniendo la cuenta de AWS. Verifique sus credenciales."
    exit 1
fi


ECR_URL="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
ECR_IMAGE_URL="$ECR_URL/$ECR_REPOSITORY_NAME"

echo "Desplegando ECR stack..."
aws cloudformation deploy \
    --template-file ecr.yml \
    --stack-name ecr-stack \
    --region $REGION

echo "Desplegando DynamoDB stack..."
aws cloudformation deploy \
    --template-file db_dynamodb.yml \
    --stack-name dynamo-stack \
    --region $REGION

echo "Haciendo login en ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

echo "Construyendo la imagen Docker..."
docker build -t $ECR_REPOSITORY_NAME .

echo "Etiquetando la imagen..."
docker tag $ECR_REPOSITORY_NAME:latest $ECR_IMAGE_URL:latest

echo "Subiendo la imagen a ECR..."
docker push $ECR_IMAGE_URL:latest

echo "Desplegando el stack principal..."
aws cloudformation deploy \
    --template-file main.yml \
    --stack-name book-stack \
    --region $REGION \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides VpcId=$VPC_ID SubnetIds=$SUBNET_IDS

echo "Proceso completado."