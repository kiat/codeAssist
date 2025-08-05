# Code Assist

## Quickstart: Linux Local Development

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5001`  

### Notes: 
Ensured that backend container is run as a non-root user, with no admin 
capabilities, and no way to increase the amount of privileges that it has
Removed the port for postgres (no longer exposed)
Created a network that all the containers can communicate with each other on 
Added gunicorn and removed the volumes the backend normally use for development



### Requirements:

- `python` ([Install](https://www.python.org/downloads/))
- `docker` ([Install](https://docs.docker.com/get-docker/))
- npm ([Install](https://nodejs.org/en/download))
- `postgresql` ([Install](https://www.postgresql.org/download/)) (Hold off on downloading this into your system until seeing the steps below)

### Setup:

1. Clone the repository (below is https)
    ```bash
    git clone https://github.com/kiat/codeAssist.git
    ```

2. Create a venv in the backend and activate it then run make install to install backend and frontend dependencies:    
    ```
    cd backend 
    python3.12 -m venv venv
    source venv/bin/activate 
    cd ..
    make install
    ```
3. Create a `.env` file in the frontend directory (don't forget to take out the curly braces)
    ```bash
    touch ./frontend/.env
    ```
    In your `.env` file, add this React environment variable:

    ```
    REACT_APP_API_URL=/api
    ```

4. go to postgres security and execute create_user.sh

5. run `docker compose up` 


6. Visit the pgadmin website via the url in the container. login with the default login:  
    `user: admin@admin.com`  
    `password: 12345`

7. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:  
    `Host name/address: db`  
    `Username: postgres`  
    `Password: postgres`  

8. In this newly created server, create a new database. Name it `codeassist`. This is important for `init_db.py`

9. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)

10. Create a `.env` file in the backend directory and add your DB connection string and restart containers 

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://postgres:postgres@db:5432/codeassist"
    ```

11. Compile the frontend using npm run build

12. install nginx:
    sudo apt update
    sudo apt install nginx

13. check that it is running with sudo systemctl status nginx

14. create a /var/www/<ip-address> and give nginx permissions to read it using 
    "sudo chown -R www-data:www-data /var/www/97.178.45.235
    sudo chmod -R 755 /var/www/97.178.45.235"
    
15. copy the build file compiled on your local machine to this file 

16. Create a config file that nginx can use in /etc/nginx/conf.d/ and add this to it
    ```
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        root /var/www/<ip-address>/build;
        index index.html;

        location / {
            try_files $uri /index.html;
        }

        location /api/ {
            proxy_pass http://localhost:5000/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }


    ```
17. run sudo rm /etc/nginx/sites-enabled/default to unlink the default website on port 80 


Notes: 
- Make sure Postgres is not running on your system (otherwise you will get errors launching the postgres container because the port will conflict). You can either uninstall postgres completely from your system or just kill the run
- Once again, if you are on macOS, make sure to turn off Airplay because it also runs on `localhost:5000`, otherwise Flask won't run!

## Testing
**As of 3/3/2025, only backend tests have started being written.

To run tests, run the the following from root directory:
```
make test
```


## Important Links (Development)
-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
