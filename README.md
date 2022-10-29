# Code Assist

## Contributors

-   Ricky Woodruff

## Important Links (Development)

-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)

---

## How to install

1. Clone the repository

```bash
git clone git@github.com:kiat/codeAssist.git
```

2. Install [Docker](https://docs.docker.com/get-docker/)

3. Install `docker-compose`

```bash
pip install docker-compose
```

4. Start the backend service

```bash
docker-compose up backend
```

5. Start the frontend service

```bash
docker-compose up frontend
```

## Done!

Your backend should now be running on `http://localhost:5000` and your frontend on `http://localhost:3000`.
