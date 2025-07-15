FROM alpine:latest

# Ensure that we are not running as root user 
RUN addgroup -S username && adduser -S -G username username

# Utilize the new user 
USER username

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
EXPOSE 5001

# Set environment variables
ENV PYTHONPATH /usr/src/app

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0" , "--port=5001"]
