# GC-AI: Local Testing Environment

This repository provides an easy way to run the [GC-AI](https://github.com/DRAGGON-Lab/GC-AI) application locally using Docker. Anyone interested in running the project on their machine can follow these simple steps.

## 🚀 Installation and Execution

### 1. **Prerequisites**
Before getting started, make sure you have installed:
- [Docker](https://www.docker.com/get-started) 🐳
- [Docker Compose](https://docs.docker.com/compose/install/) (already included in Docker Desktop)

You can check if Docker is installed by running:
```sh
docker --version
```
And for Docker Compose:
```sh
docker compose version
```

You also need about **14 GB of free disk space** for the images (a 4.5 GB download that unpacks to roughly 14 GB, most of it the backend's machine learning dependencies), and a machine with at least 4 GB of RAM available to Docker. The images are built for `linux/amd64`, so on Apple Silicon and other arm64 hosts they run under emulation: everything works, but detection and startup are slower.

### 2. **Download the Project**
Clone the repository or download the `docker-compose.yml` file into a local folder:

- Using SSH:
  ```sh
  git clone git@github.com:DRAGGON-Lab/GC-AI-environment.git
  cd GC-AI-environment
  ```

- Using HTTPS (no SSH key required):
  ```sh
  git clone https://github.com/DRAGGON-Lab/GC-AI-environment.git
  cd GC-AI-environment
  ```

### 3. **Run the Project**
In the same folder where `docker-compose.yml` is located, run:
```sh
docker compose up -d --wait
```
This downloads the images and starts the services. `--wait` returns only once the database and the backend both report healthy, which means the backend is serving, the detection model is loaded, and the parts database answers queries — so when the command finishes, the application is ready to use.

The first start takes a while: the images download, then MySQL initialises and the backend loads the detection model.

To watch what is happening while it comes up:
```sh
docker compose logs -f backend
```

### 4. **Check the Installation**
```sh
./smoke-test.sh
```
This confirms the parts database returns data, that one known part comes back with its sequence, and that the web interface responds. It prints the URL to open when everything passes, and the relevant `docker compose logs` command when something does not.

The API's own `/healthcheck/` endpoint reports `500` in this build whatever the state of the service, because it closes its database cursor without reading the result of its test query. Use the smoke test, or `docker compose ps`, to check whether the stack is up.

### 5. **Access the Application**
- **Frontend:** [http://localhost:8081](http://localhost:8081)
- **Backend API:** [http://localhost:5001](http://localhost:5001)
- **Database:** MySQL on port `3307` (user `root`, password `igemparts2024`)

### 6. **Changing Ports and the Database Password**
Copy `.env.example` to `.env` and edit the values:
```sh
cp .env.example .env
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `FRONTEND_PORT` | `8081` | Host port for the web interface |
| `BACKEND_PORT` | `5001` | Host port for the backend API |
| `DB_PORT` | `3307` | Host port for MySQL |
| `DB_PASSWORD` | `igemparts2024` | MySQL root password |

Then apply them:
```sh
docker compose up -d --wait
```

🚨 **The web interface requires the backend on host port 5001.** The frontend bundle has `http://localhost:5001` compiled in, so a different `BACKEND_PORT` leaves the API reachable on the new port while the web interface can no longer reach it. Change it only when you are calling the API directly.

`DB_PASSWORD` applies to a new database volume. To change it on an existing installation, remove the volume first with `docker compose down -v`.

### 7. **Handling Port Conflicts**
If a port is already in use, set a different one in `.env` as described above.

To find out what is holding a port:
```sh
lsof -i :<PORT>                 # macOS
ss -tulpn | grep :<PORT>        # Linux
netstat -ano | findstr :<PORT>  # Windows
```
Replace `<PORT>` with the port number in question (for example 5001, 8081, or 3307).

To stop the process using it:
```sh
kill -9 <PID>           # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

### 8. **Stop the Application**
To stop the services, use:
```sh
docker compose down
```
To also remove volumes and the database:
```sh
docker compose down -v
```

## 📌 Notes
- No manual configuration is required — everything is ready to run with Docker.
- The images are pinned by digest, so every installation runs the exact same build. The tag each digest corresponds to is in a comment above it in `docker-compose.yml`.
- To pick up a newer published build, run `docker compose pull` after updating the digests.
- If something fails to start, `docker compose ps` shows which service is unhealthy and `docker compose logs <service>` shows why.
