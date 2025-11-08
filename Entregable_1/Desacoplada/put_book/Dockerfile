# post_book/Dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copiar solo el handler
COPY handler.py ${LAMBDA_TASK_ROOT}/


CMD ["handler.lambda_handler"]