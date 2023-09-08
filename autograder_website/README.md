# Notes from allen
the .env file may need to change for you. It could be one of two strings:
1. DB_CONNECTION_STRING="postgresql://root:root@localhost:5432/test_db"
2. DB_CONNECTION_STRING="postgresql://root:root@host.docker.internal:5432/test_db"

## Using pgAdmin container
1. Go to url where it is hosted (access this from docker client or [here](http://localhost:5050))
2. Right click the server dropdown and register a server
3. Create a name for the server. Something like autograder_backend
4. Under the connection tab there is a field for Host name/address. set this to ```host.docker.internal``` (this is because we are communicating between two docker containers)
5. Set username and password in connections tab to whatever it is in the docker-compose.yml (currently set to root and root for me)

This should create the connection to the database. Make sure to run init_db.py in the [backend](./backend/) folder to create the tables. Creating the tables new will make you LOSE ALL PREVIOUS DATA.