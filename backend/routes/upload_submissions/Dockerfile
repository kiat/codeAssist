FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y unzip

WORKDIR /app

RUN pip install pylint gradescope_utils

# Use an ARG to receive the hash_str build argument
ARG HASH_STR

# Assuming your build context is the root of the Flask app and the `routes` directory is directly under the root
COPY ./routes/upload_submissions/runs/${HASH_STR}/${FILENAME}/test_cases ./
COPY ./routes/upload_submissions/runs/${HASH_STR}/test_cases ./test_cases
COPY ./routes/upload_submissions/Entrypoint.sh ./Entrypoint.sh
COPY ./routes/upload_submissions/studentgrader.py ./studentgrader.py

RUN chmod +x ./Entrypoint.sh

ENTRYPOINT ["./Entrypoint.sh"]
