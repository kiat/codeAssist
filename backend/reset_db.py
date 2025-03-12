import subprocess
import psycopg2
from dotenv import load_dotenv
import os

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

# Test the connection to the PostgreSQL database
def test_connection(user, password, host, port, db_name):
    try:
        conn = psycopg2.connect(
            dbname=db_name, user=user, password=password, host=host, port=port
        )
        print("Connection successful.")
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False
    return True

# Function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr.decode())
    else:
        print(result.stdout.decode())

# Check if the user exists in the database
def check_user_exists(cursor, user):
    cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{user}'")
    return cursor.fetchone() is not None

# Main function to reset the database
def reset_database():
    # Parse the connection string
    user, password, host, port, db_name = parse_connection_string(DB_CONNECTION_STRING)

    # Test connection to the database using the 'codeassistapi' user
    if not test_connection(user, password, host, port, db_name):
        return

    # Drop the database using sudo -u postgres
    print(f"Dropping database {db_name}...")
    run_command(f"sudo -u postgres psql -c 'DROP DATABASE IF EXISTS {db_name};'")

    # Recreate the database using sudo -u postgres
    print(f"Creating database {db_name}...")
    run_command(f"sudo -u postgres psql -c 'CREATE DATABASE {db_name};'")

    # Grant ownership of the database to 'codeassistapi'
    print(f"Changing ownership of database {db_name} to 'codeassistapi'...")
    run_command(f"sudo -u postgres psql -c 'ALTER DATABASE {db_name} OWNER TO codeassistapi;'")

    # Run the init_db.py script to create the tables
    print("Running init_db.py to create the tables...")
    run_command("python init_db.py")

if __name__ == "__main__":
    reset_database()
