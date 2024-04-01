FROM python:3.9

# Upgrade pip
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


# 'assignments/assignment1/Dockerfile.zip'
