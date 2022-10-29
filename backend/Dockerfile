FROM alpine:latest

# Add pip and python
RUN apk update
RUN apk add py-pip
RUN apk add --no-cache python3-dev 
RUN pip install --upgrade pip

# Copy and install requirements
WORKDIR /usr/app
COPY ./requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt

# Copy app
COPY . .

EXPOSE 5000

ENV PYTHONPATH /usr/app

# Start app
CMD [ "flask", "run", "--host=0.0.0.0" ]