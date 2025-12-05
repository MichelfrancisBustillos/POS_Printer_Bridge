# POS Printer Bridge

[![PyLint](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/python_linting.yml/badge.svg)](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/python_linting.yml)

A small Python HTTP API to send text and QR codes to an ESC/POS-compatible receipt printer on the network.

This project exposes a minimal FastAPI service with endpoints for printing plain text and QR codes. It uses `python-escpos` (the `escpos` package) to communicate with network printers.

## Highlights

- **Print text** via POST to `/print_text/` with query parameters.
- **Print QR codes** via POST to `/print_qr/` with query parameters.
- Easy configuration via environment variables or a `.env` file.
- Docker support via `Dockerfile` / `docker-compose.yml`.

## Requirements

- Python 3.10+ (project uses modern typing features)
- A network-capable ESC/POS printer reachable from the host running the API
- `requirements.txt` contains required Python packages

## Quick Start (local)

1. Clone the repo and create a virtual environment:

    ```powershell
    git clone https://github.com/MichelfrancisBustillos/POS_Printer_Bridge.git
    cd POS_Printer_Bridge
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

2. Configure your printer by creating a `.env` file in the project root (or set environment variables):

    ```text
    PRINTER_IP=192.168.1.100
    PRINTER_PROFILE=TM-T88V
    ```

3. Run the API:

    ```powershell
    python main.py
    ```

By default the API runs on `http://0.0.0.0:8000`.

## Docker (optional)

Build and run using Docker Compose:

```powershell
docker-compose up --build
```

The compose file will run the service on port `8000` by default.

## Environment variables
- `PRINTER_IP` - IPv4 address of your receipt printer (required at runtime).
- `PRINTER_PROFILE` - Optional ESC/POS profile name used by `escpos.printer.Network`.

If the `.env` file is present the app loads it at startup.

## API Endpoints

- `GET /` — Health check. Returns a simple JSON message.
- `GET /config` — Returns current configured `ip` and `profile` (from environment).
- `POST /print_text/` — Print plain text. Accepts query parameters (see examples).
- `POST /print_qr/` — Print a QR code. Accepts query parameters (see examples).

Note: the endpoints accept a `Payload` via query parameters (the FastAPI implementation uses `Query()` for the fields). The `Payload` fields are:

- `content` (string) — Text or QR payload to print (required).
- `copies` (int, >=1) — Number of copies to print (default: `1`).
- `size` (int, 1-16) — Font/QR size (default: `8` for text; used by QR endpoint).
- `cut` (bool) — Cut paper after each copy (default: `True`).

## Examples

Using `curl` (POST with query string):

```powershell
curl -X POST "http://localhost:8000/print_text/?content=Hello%20Printer&copies=1&cut=true"

curl -X POST "http://localhost:8000/print_qr/?content=https%3A%2F%2Fexample.com&size=4&copies=1&cut=true"
```

Using Python `requests`:

```python
import requests

base = "http://localhost:8000"

# Print text
payload = {"content": "Hello from API", "copies": 1, "cut": True}
resp = requests.post(f"{base}/print_text/", params=payload)
print(resp.status_code, resp.json())

# Print QR
payload = {"content": "https://example.com", "size": 4, "copies": 1, "cut": True}
resp = requests.post(f"{base}/print_qr/", params=payload)
print(resp.status_code, resp.json())
```

## Troubleshooting

- If the server raises "No .env file found. Exiting.", create a `.env` file with `PRINTER_IP` set.
- Ensure the printer is reachable from the host (ping the `PRINTER_IP`).
- Confirm the `escpos` package supports your printer model; you may need to set `PRINTER_PROFILE`.
