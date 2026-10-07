# CodeAssist: Linux Server Deployment

This guide sets up CodeAssist on a fresh Ubuntu server so students and instructors can reach it over the internet. It was written and tested on a Google Compute Engine VM running Ubuntu 26.04 LTS, but steps 2 onward work on any Ubuntu server.

For local development on your own machine, use the root `README.md` instead.

## What you end up with

```
browser ──HTTP:80──> nginx ──┬── /        → React build in /var/www/codeassist/build
                             └── /api/*   → Flask backend on 127.0.0.1:5001 (Docker)
                                                  ├── Postgres  127.0.0.1:5432 (Docker)
                                                  └── pgAdmin   127.0.0.1:5050 (Docker)
```

Only nginx (port 80) is reachable from the internet. The backend, Postgres and pgAdmin listen on `127.0.0.1` only.

## 1. Create the VM (Google Cloud)

1. Compute Engine > VM instances > **Create instance**.
2. **Machine configuration:** name `codeassist`, pick a region near your users, series **E2**, machine type **e2-standard-4** (4 vCPU, 16 GB). Autograding runs a Docker container per submission, so smaller machines struggle when many students submit at once.
3. **OS and storage > Change:** Operating system **Ubuntu**, version **Ubuntu 26.04 LTS (x86/64)**, size **100 GB**. The version list also contains 22.04, 24.04, Minimal and Arm images, so read the label carefully. After creating, the SSH banner should say `Welcome to Ubuntu 26.04`.
4. **Networking:**
   - Tick **Allow HTTP traffic** and **Allow HTTPS traffic**.
   - Open the network interface, set **External IPv4 address** to **Reserve static external IP address**, and name it (e.g. `codeassist-ip`). A static IP survives VM restarts, so the URL you hand out keeps working. If you recreate the VM later, select the existing reservation instead of reserving a new one.
5. **Create**, then click **SSH** on the VM row.

Do not add firewall rules for ports 5001, 5432 or 5050. Use an SSH tunnel to reach pgAdmin (see [Day-to-day](#day-to-day)).

## 2. Base packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y htop git tmux python3-venv python3-pip nginx curl ca-certificates
```

If a "Pending kernel upgrade" or "Which services should be restarted?" screen appears, press Enter to accept the defaults. If the login banner later says `*** System restart required ***`, run `sudo reboot` and reconnect.

## 3. Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

If `apt update` reports that the Docker repository has no Release file for your Ubuntu version, use Ubuntu's packages instead:

```bash
sudo rm /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

Let your user run Docker without sudo, then **close the SSH window and open a new one** so the group change applies:

```bash
sudo usermod -aG docker $USER
```

Check:

```bash
docker run --rm hello-world
docker compose version     # needs v2.24.4 or newer for the override file in step 6
```

## 4. Node.js and the repo

```bash
sudo apt install -y nodejs npm
node -v                    # 18 to 22 works with react-scripts 5

cd ~
git clone https://github.com/kiat/codeAssist.git
cd codeAssist
```

Every `docker compose` command below must be run from `~/codeAssist`. A new SSH session starts in `~`, so `cd ~/codeAssist` first or you get `no configuration file provided: not found`.

## 5. Backend environment

Run steps 5 and 6 in the same SSH session, since step 6 reuses `$DB_PASS`.

```bash
cd ~/codeAssist
EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
DB_PASS=$(openssl rand -hex 16)
echo "External IP: $EXTERNAL_IP"

cat > backend/.env <<EOF
DB_CONNECTION_STRING=postgresql+psycopg2://postgres:${DB_PASS}@db:5432/codeassist
SECRET_KEY=$(openssl rand -hex 32)
API_SECRET_KEY=$(python3 -c 'import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())')
PASSWORD_SALT=$(openssl rand -hex 16)
FRONTEND_ORIGIN=http://${EXTERNAL_IP}
EOF
chmod 600 backend/.env
```

The metadata URL only works on Google Cloud. Elsewhere, set `EXTERNAL_IP` to the server's public IP by hand.

| Variable | Purpose |
|---|---|
| `DB_CONNECTION_STRING` | Postgres URL. `db` is the Compose service name. |
| `SECRET_KEY` | Signs session cookies. The backend refuses to start without it. |
| `API_SECRET_KEY` | Fernet key that encrypts instructors' stored AI provider keys. Losing it makes stored keys unreadable. |
| `PASSWORD_SALT` | Used in password hashing. Changing it later invalidates existing passwords. |
| `FRONTEND_ORIGIN` | The one origin allowed by CORS. Use `https://...` once HTTPS is set up. |

Back up `backend/.env` somewhere safe. It is the only copy of these secrets.

## 6. Lock down Docker ports and passwords

```bash
cp docs/Linux-Installation/docker-compose.server.yml docker-compose.override.yml
sed -i "s/CHANGE_ME_DB_PASSWORD/${DB_PASS}/; s/CHANGE_ME_PGADMIN_PASSWORD/$(openssl rand -hex 12)/" docker-compose.override.yml
grep -c CHANGE_ME docker-compose.override.yml   # should print 0
```

Compose loads `docker-compose.override.yml` automatically on top of `docker-compose.yml`. The override:

- binds the backend, Postgres and pgAdmin to `127.0.0.1`. Docker-published ports skip `ufw`, so without this they are open to the internet whenever the cloud firewall allows it;
- turns off Flask debug mode;
- replaces the default `postgres` and `12345` passwords. Find the pgAdmin one later with `grep PGADMIN docker-compose.override.yml`.

## 7. Start the backend and create tables

```bash
docker compose up -d --build
sleep 5
docker compose ps                  # all three containers should be "Up"
docker compose exec backend python3 init_db.py
docker compose exec backend flask db stamp heads
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5001/    # 404 is fine, 000 means not running
```

- The `codeassist` database is created automatically by the Postgres container. You do not need pgAdmin for setup.
- `init_db.py` **drops every table** before creating them. Run it only on a fresh install, never on a server with real data.
- `flask db stamp heads` records that the schema matches the latest migration, so future updates can use `flask db upgrade`.
- A `SESSION_COOKIE_SECURE is not set to true` warning in the logs is expected until HTTPS is set up.

## 8. Build the frontend

```bash
cd ~/codeAssist/frontend
echo 'REACT_APP_API_URL=/api' > .env
npm install
npm run build
```

`npm install` prints many deprecation warnings; those are fine. The build should end with "Compiled successfully" or "Compiled with warnings". `REACT_APP_API_URL` is baked in at build time, so rebuild after changing it.

## 9. nginx

```bash
sudo mkdir -p /var/www/codeassist
sudo rm -rf /var/www/codeassist/build
sudo cp -r ~/codeAssist/frontend/build /var/www/codeassist/
sudo chown -R www-data:www-data /var/www/codeassist

sudo cp ~/codeAssist/docs/Linux-Installation/nginx-codeassist.conf /etc/nginx/conf.d/codeassist.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

`nginx -t` must print `test is successful`. If it fails, the reload is skipped and nginx keeps serving its "Welcome to nginx!" page.

## 10. Verify

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/        # 200, the React app
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/api/    # 404 from Flask, proxied by nginx
```

Then open `http://<static IP>` in a browser (use a private window or hard refresh to skip a cached nginx page) and sign up.

## Day-to-day

**Deploying a new version**

```bash
cd ~/codeAssist
git pull
docker compose up -d --build
docker compose exec backend flask db upgrade
cd frontend && npm install && npm run build
sudo rm -rf /var/www/codeassist/build && sudo cp -r build /var/www/codeassist/ && sudo chown -R www-data:www-data /var/www/codeassist
```

**pgAdmin** (from your laptop, with the [gcloud CLI](https://cloud.google.com/sdk/docs/install)):

```bash
gcloud compute ssh codeassist --zone <zone> -- -L 5050:localhost:5050
```

Then open `http://localhost:5050`. In pgAdmin, register a server with host `db`, user `postgres`, and the password from `DB_CONNECTION_STRING`.

**Logs:** `docker compose logs backend --tail 100`, `sudo tail -50 /var/log/nginx/error.log`.

## Checking for compromise

A public IP gets scanned within minutes of going live. Check periodically:

- `htop`, press `P` to sort by CPU. When idle, everything should be near 0%. Warning signs: sustained high CPU with no users, unfamiliar process names (`xmrig`, `kdevtmpfsi`, random strings), anything running from `/tmp`, or processes owned by users you did not create.
- `sudo ss -tulpn` lists listening ports. Only nginx (`:80`), sshd (`:22`), and `127.0.0.1`-bound Docker ports should appear.
- `last` shows recent logins. `sudo journalctl -u ssh | grep -i failed | tail` shows SSH brute-force attempts, which are normal background noise.

Never run `init_db.py`, remove the override file, or open firewall ports for 5001/5432/5050 on a live server.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `sudo: I'm sorry <user>. I'm afraid I can't do that` (or `may not run sudo`) | On GCE, SSH-in-browser adds a temporary key and the guest agent removes you from `google-sudoers` when it expires, even if your window is still open. `getent group google-sudoers` will not list you. Close the window and open a new SSH session. For long sessions use `gcloud compute ssh`. |
| Backend `Exited`, logs show `No module named 'psycopg'` | SQLAlchemy 2.1+ maps `postgresql://` to psycopg 3. `requirements.txt` pins SQLAlchemy below 2.1, and the connection string above names `psycopg2` explicitly. Rebuild with `docker compose up -d --build`. |
| `service "backend" is not running` | Run `docker compose logs backend --tail 60` and read the traceback. |
| `no configuration file provided: not found` | You are not in `~/codeAssist`. |
| Browser shows "Welcome to nginx!" | `nginx -t` failed or the default site is still enabled. Rerun step 9 and read the `nginx -t` output. |
| Pages load but login fails | Check that `frontend/.env` has `REACT_APP_API_URL=/api` and that you rebuilt and recopied the frontend. |
| Uploads fail with `413 Request Entity Too Large` | `client_max_body_size` is missing from the nginx config. |

## Other files in this folder

`create_user.sh`, `pg_hba.conf` and `postgresql.conf` are from an earlier hardening attempt and are not used by the current `docker-compose.yml`. They are kept for reference.
