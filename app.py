from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import random
import socket
import threading
import time
from urllib.parse import parse_qs, urlparse

START_TIME = time.time()

CONFIG = {
    "service_name": os.getenv("SERVICE_NAME", "cloud-telemetry-demo"),
    "env": os.getenv("APP_ENV", "local"),
    "region": os.getenv("CLOUD_REGION", "ap-south-1"),
    "port": int(os.getenv("PORT", "8080")),
    "error_rate": float(os.getenv("ERROR_RATE", "0.0")),  # 0.0 to 1.0
}

METRICS_LOCK = threading.Lock()
METRICS = {
    "total_requests": 0,
    "error_requests": 0,
    "by_path": {},
    "last_latency_ms": 0.0,
}


def record_metric(path: str, latency_ms: float, is_error: bool = False) -> None:
    with METRICS_LOCK:
        METRICS["total_requests"] += 1
        if is_error:
            METRICS["error_requests"] += 1
        METRICS["by_path"][path] = METRICS["by_path"].get(path, 0) + 1
        METRICS["last_latency_ms"] = round(latency_ms, 2)


class CloudHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Served-By", socket.gethostname())
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        t0 = time.perf_counter()
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Optional simulated chaos / error rate for testing resilience
        if random.random() < CONFIG["error_rate"]:
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms, is_error=True)
            self._send_json(
                503,
                {
                    "status": "error",
                    "message": "Simulated transient cloud failure",
                    "host": socket.gethostname(),
                },
            )
            return

        if path == "/":
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms)
            self._send_json(
                200,
                {
                    "service": CONFIG["service_name"],
                    "environment": CONFIG["env"],
                    "region": CONFIG["region"],
                    "host": socket.gethostname(),
                    "endpoints": {
                        "home": "/",
                        "health": "/health",
                        "metrics": "/metrics",
                        "work": "/work?delay_ms=100",
                    },
                },
            )

        elif path == "/health":
            uptime_sec = round(time.time() - START_TIME, 2)
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms)
            self._send_json(
                200,
                {
                    "status": "healthy",
                    "uptime_seconds": uptime_sec,
                    "host": socket.gethostname(),
                    "environment": CONFIG["env"],
                },
            )

        elif path == "/metrics":
            load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
            with METRICS_LOCK:
                snapshot = {
                    "total_requests": METRICS["total_requests"],
                    "error_requests": METRICS["error_requests"],
                    "by_path": dict(METRICS["by_path"]),
                    "last_latency_ms": METRICS["last_latency_ms"],
                }
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms)
            self._send_json(
                200,
                {
                    "host": socket.gethostname(),
                    "uptime_seconds": round(time.time() - START_TIME, 2),
                    "load_average_1m_5m_15m": [round(x, 2) for x in load_avg],
                    "requests": snapshot,
                },
            )

        elif path == "/work":
            try:
                delay_ms = float(query.get("delay_ms", ["50"])[0])
                delay_ms = max(0.0, min(delay_ms, 5000.0))  # Cap at 5s
            except ValueError:
                delay_ms = 50.0

            time.sleep(delay_ms / 1000.0)
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms)
            self._send_json(
                200,
                {
                    "status": "completed",
                    "simulated_work_ms": delay_ms,
                    "actual_elapsed_ms": round(latency_ms, 2),
                    "processed_by": socket.gethostname(),
                },
            )

        else:
            latency_ms = (time.perf_counter() - t0) * 1000
            record_metric(path, latency_ms, is_error=True)
            self._send_json(404, {"status": "not_found", "path": path})

    def log_message(self, format: str, *args) -> None:
        # Structured-style stdout log line (captured by Docker logs)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"[{timestamp}] {self.address_string()} - {format % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", CONFIG["port"]), CloudHandler)
    print(
        f"Starting {CONFIG['service_name']} on 0.0.0.0:{CONFIG['port']} "
        f"(env={CONFIG['env']}, region={CONFIG['region']})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()