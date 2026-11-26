# Cloud Health & Telemetry Microservice (`cloud-telemetry-demo`)

A lightweight, single-file cloud-native microservice built with Python's standard library and containerized with Docker. It demonstrates health/liveness checks, runtime telemetry, environment-based configuration, simulated latency, and transient failure injection with zero external dependencies.

## Features

- **Zero External Dependencies:** Uses only Python's built-in standard library (`http.server`, `os`, `json`, `time`, `socket`, `threading`, `urllib.parse`).
- **Environment-Driven Configuration:** Configured at runtime via environment variables (`SERVICE_NAME`, `APP_ENV`, `CLOUD_REGION`, `PORT`, `ERROR_RATE`).
- **Health & Telemetry Endpoints:** Exposes JSON endpoints for service discovery, liveness checks, simulated workload delay, and request/latency metrics.
- **Container-Ready:** Built on `python:3.12-slim` with unbuffered `stdout` logging, a non-root user (`appuser`), and a `HEALTHCHECK` instruction.

## Project Structure

```text
cloud-telemetry-demo/
├── app.py           # Single-file HTTP server, metrics tracker, and endpoints
├── Dockerfile       # Container build instructions
├── .dockerignore    # Files excluded from the Docker build context
└── README.md        # Project documentation
```

## Endpoints

| Endpoint | Description | Example |
| :--- | :--- | :--- |
| `GET /` | Returns service name, environment, region, container hostname, and route list | `http://127.0.0.1:8080/` |
| `GET /health` | Returns liveness status (`healthy`), uptime in seconds, hostname, and environment | `http://127.0.0.1:8080/health` |
| `GET /work?delay_ms=150` | Simulates processing delay (`0` to `5000` ms, default `50` ms) and reports elapsed time | `http://127.0.0.1:8080/work?delay_ms=150` |
| `GET /metrics` | Returns total requests, `503` error count, hits per path, last latency (ms), and load average | `http://127.0.0.1:8080/metrics` |

## Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SERVICE_NAME` | `cloud-telemetry-demo` | Logical service identifier returned by `/` |
| `APP_ENV` | `local` | Environment label (`local`, `staging`, `cloud`) |
| `CLOUD_REGION` | `ap-south-1` | Target region label returned by `/` |
| `PORT` | `8080` | TCP port the HTTP server listens on |
| `ERROR_RATE` | `0.0` | Probability (`0.0` to `1.0`) of returning a simulated `503` error |

## Run Locally (Without Docker)

In PowerShell:

```powershell
$env:APP_ENV="dev"
$env:CLOUD_REGION="local-dev"
$env:PORT="8080"
$env:ERROR_RATE="0.0"
python3 app.py
```

Test the endpoints in a second PowerShell window:

```powershell
Invoke-RestMethod -Uri "[http://127.0.0.1:8080/](http://127.0.0.1:8080/)"
Invoke-RestMethod -Uri "[http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)"
Invoke-RestMethod -Uri "[http://127.0.0.1:8080/work?delay_ms=150](http://127.0.0.1:8080/work?delay_ms=150)"
Invoke-RestMethod -Uri "[http://127.0.0.1:8080/metrics](http://127.0.0.1:8080/metrics)"
```

## Build and Run with Docker

1. **Build the image:**

   ```powershell
   docker build -t cloud-telemetry-demo:1.0 .
   ```

2. **Run the container:**

   ```powershell
   docker run -d --name telemetry-svc -p 8080:8080 -e APP_ENV=staging -e CLOUD_REGION=ap-south-1 -e ERROR_RATE=0.0 cloud-telemetry-demo:1.0
   ```

3. **Verify status, logs, and endpoints:**

   ```powershell
   docker ps
   docker logs telemetry-svc
   Invoke-RestMethod -Uri "[http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)"
   Invoke-RestMethod -Uri "[http://127.0.0.1:8080/metrics](http://127.0.0.1:8080/metrics)"
   ```

## Cleanup

Stop and remove the container (and optionally remove the image):

```powershell
docker stop telemetry-svc
docker rm telemetry-svc
docker rmi cloud-telemetry-demo:1.0
```
