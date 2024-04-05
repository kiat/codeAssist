# Use Python official image as the base
FROM python:3.8-slim

# Set environment variable to keep Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# Set environment variable to buffer Python output in Docker logs
ENV PYTHONUNBUFFERED 1

# Install additional dependencies needed to handle ZIP files
RUN apt-get update && apt-get install -y unzip

ENV PYTHONPATH "${PYTHONPATH}:/app"

# Set the working directory to /app
WORKDIR /app

# Install Python dependencies
RUN pip install pylint gradescope_utils 

COPY ./runs/${ASSIGNMENT_ID}/${FILENAME} /app/${FILENAME}

COPY Entrypoint.sh /app/Entrypoint.sh
COPY autograder.py /app/autograder.py

RUN chmod +x /app/Entrypoint.sh

ENTRYPOINT ["/app/Entrypoint.sh"]
