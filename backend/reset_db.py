import subprocess
import psycopg2
from dotenv import load_dotenv
import os

# Constant for the service account user which will be the owner of the database
DB_OWNER_USER = "codeassistapi"  # Name of the user set as the owner of the 'codeassist' DB

# Load environment variables from .env
load_dotenv()

# Retrieve the connection string from the environment
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# Parse the connection string to get database credentials
def parse_connection_string(conn_str):
    parts = conn_str.replace("postgresql://", "").split("@")
    user_password = parts[0].split(":")
    user = user_password[0]
    password = user_password[1]
    host_db = parts[1].split(":")
    host = host_db[0]
    port_db = host_db[1].split("/")
    port = port_db[0]
    db_name = port_db[1]
    return user, password, host, port, db_name

# Test the connection to the PostgreSQL instance
def test_connection_to_instance(user, password, host, port):
    print(f"Testing connection to PostgreSQL instance as {user}...")
    try:
        conn = psycopg2.connect(
            dbname="postgres", user=user, password=password, host=host, port=port
        )
        print("Connection successful.")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL instance: {e}")
        return False
    return True

# Function to run shell commands with debug output
def run_command(command):
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"stderr: {result.stderr.decode()}")
    else:
        print(f"stdout: {result.stdout.decode()}")

# Check if the user exists using sudo -u postgres psql
def check_user_exists(user):
    print(f"Checking if the user {user} exists using 'sudo -u postgres psql'...")
    command = f"sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{user}';\""
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Error running check user command: {result.stderr.decode()}")
        return False
    
    exists = result.stdout.decode().strip() == '1'
    print(f"User {user} exists: {exists}")
    return exists

# Main function to reset the database
def reset_database():
    print("Starting the database reset process...")

    # Parse the connection string
    user, password, host, port, db_name = parse_connection_string(DB_CONNECTION_STRING)

    # Test connection to the PostgreSQL instance (not a specific database)
    if not test_connection_to_instance(user, password, host, port):
        print("Connection test failed. Exiting.")
        return

    # Check if the user 'DB_OWNER_USER' exists before creating the database
    if not check_user_exists(DB_OWNER_USER):
        print(f"Error: The user '{DB_OWNER_USER}' does not exist in the PostgreSQL instance.")
        return

    # Drop the database using sudo -u postgres
    print(f"Dropping database {db_name} if it exists...")
    run_command(f"sudo -u postgres psql -c 'DROP DATABASE IF EXISTS {db_name};'")

    # Recreate the database and set the owner in one command using sudo -u postgres
    print(f"Creating database {db_name} and setting ownership to '{DB_OWNER_USER}'...")
    run_command(f"sudo -u postgres psql -c 'CREATE DATABASE {db_name} OWNER {DB_OWNER_USER};'")

    # Run the init_db.py script to create the tables
    print("Running init_db.py to create the tables...")
    run_command("python init_db.py")

    print("Database reset process completed successfully.")

if __name__ == "__main__":
    reset_database()
