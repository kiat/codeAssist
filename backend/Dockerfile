FROM alpine:latest

#Install Python, pip, and Docker
RUN apk add --no-cache python3 py3-pip docker


RUN addgroup -g 1000 appgroup && adduser -D -u 1000 -G appgroup appuser

# Set the working directory in the container
WORKDIR /usr/src/app


# Copy migrations
COPY migrations /usr/src/app/migrations

RUN chown -R appuser:appgroup /usr/src/app

USER appuser 

# Copy the Python requirements file and install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages && pip3 show flask

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Set environment variables
ENV PYTHONPATH /usr/src/app

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0" , "--port=5001"]
