FROM alpine:latest

# Install Python, pip, and Docker
RUN apk add --no-cache python3 py3-pip docker

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the database migrations
COPY migrations /usr/src/app/migrations

# Copy the Python requirements file and install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH /usr/src/app

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]