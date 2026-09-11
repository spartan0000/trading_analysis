FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY pipeline/ ./pipeline/
COPY data/tickers.csv ./data/tickers.csv
COPY lambda_function.py .

CMD ["lambda_function.handler"]