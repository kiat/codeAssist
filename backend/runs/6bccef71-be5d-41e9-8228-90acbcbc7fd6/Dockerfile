FROM alpine:latest

RUN apk update
RUN apk add py-pip
RUN apk add --no-cache python3-dev 
RUN pip install --upgrade pip

WORKDIR /usr/app/src

COPY Spiral.py requirements.txt run_tests.py ./

COPY a1_test_cases/ ./a1_test_cases/
COPY tests/ ./tests/

RUN pip --no-cache-dir install -r requirements.txt

ENV PYTHONPATH /usr/app

CMD ["python3", "run_tests.py"]