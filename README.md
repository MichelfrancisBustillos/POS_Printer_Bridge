# POS Printer Bridge

[![PyLint](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/python_linting.yml/badge.svg)](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/python_linting.yml) [![Docker Test](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/docker_test.yml/badge.svg)](https://github.com/MichelfrancisBustillos/POS_Printer_Bridge/actions/workflows/docker_test.yml)

A small Python HTTP API to send text, QR codes, barcodes, and images to an ESC/POS-compatible receipt printer on the network.

This project exposes a minimal FastAPI service with endpoints for printing plain text and QR codes. It uses `python-escpos` (the `escpos` package) to communicate with network printers.

## Quick Start

### Prerequisites

1. Ensure you have Python 3.8+ installed (if using local setup) or Docker installed (if using Docker).
2. Have access to an ESC/POS-compatible receipt printer (network, serial, or USB).
3. Create a `.env` file in the project root with the correct environment variables (see below).
   1. `PRINTER_TYPE` - Type of printer connection: `network`, `serial`, `usb`, or `dummy`.
   2. For `network` printers, set `PRINTER_IP` to the printer's IP address.
   3. For `serial` printers, set `PRINTER_PORT` to the serial port (e.g., `/dev/tty0` on Linux or `COM1` on Windows).
   4. For `usb` printers, set `PRINTER_VENDOR_ID` and `PRINTER_PRODUCT_ID` to the USB device path.
        - Find these IDs using `lsusb` on Linux or `usb-devices` command.

        ```bash
        lsusb
            Bus 002 Device 001: ID 04b8:0202 Epson ...
        # Here, `04b8` is the Vendor ID and `0202` is the Product ID.
        lsusb -vvv -d xxxx:xxxx | grep iInterface
            iInterface 1
        # The interface number ('1') is also needed for some printers.
        ```

### Local Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/MichelfrancisBustillos/POS_Printer_Bridge.git
    cd POS_Printer_Bridge
    ```

2. Create and activate a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the server:

    ```bash
    python src/main.py
    ```

### Docker Build Setup

1. Build and run the Docker container using Docker Compose:

    ```bash
    docker compose up --build -d
    ```

## Environment variables

| Environment Variable     | Required | Printer Type | Default | Description                                                                                                    |
|--------------------------|----------|--------------|---------|----------------------------------------------------------------------------------------------------------------|
| PRINTER_TYPE             | **Yes**  | All          |         | 'network', 'usb', 'serial', 'dummy'                                                                            |
| PRINTER_PROFILE          | Optional | All          |         | See [ESCPOS Profiles](https://python-escpos.readthedocs.io/en/latest/printer_profiles/available-profiles.html) |
| PRINTER_IP               | **Yes**  | Network      |         | IP of Networked Printer                                                                                        |
| PRINTER_USB_VENDOR_ID    | **Yes**  | USB          |         | Vendor ID for USB Printer                                                                                      |
| PRITNER_USB_PRODUCT_ID   | **Yes**  | USB          |         | Product ID for USB Printer                                                                                     |
| PRINTER_USB_INTERFACE    | Optional | USB          | 0       | USB Interface                                                                                                  |
| PRINTER_USB_ENDPOINT_OUT | Optional | USB          | 0x01    | USB Output Endpoint                                                                                            |
| PRINTER_SERIAL_PORT      | **Yes**  | Serial       |         | Serial Port                                                                                                    |
| PRINTER_SERIAL_BAUDRATE  | Optional | Serial       | 9600    | Baud rate for serial transmission                                                                              |
| PRINTER_SERIAL_BYTESIZE  | Optional | Serial       | 8       | Serial buffer size                                                                                             |
| PRINTER_SERIAL_PARITY    | Optional | Serial       | N       | Parity Checking                                                                                                |
| PRINTER_SERIAL_STOPBITS  | Optional | Serial       | 1       | Number of stop bits                                                                                            |
| PRINTER_SERIAL_TIMEOUT   | Optional | Serial       | 1       | Read/write timeout in seconds                                                                                  |
| PRITNER_SERIAL_DSRDTR    | Optional | Seral        | True    | Hardware flow control (False to enable RTS/CTS)                                                                |
| PRINTER_ALIGNMENT        | Optional | All          | Left    | 'left', 'center', 'right' justification                                                                        |
| PRINTER_FONT             | Optional | All          | a       | 'a' or 'b', not available on all printers                                                                      |
| PRINTER_BOLD             | Optional | All          | False   |                                                                                                                |
| PRINTER_UNDERLINE        | Optional | All          | 0       | '0' (no underline), '1' (single underline), '2' (double underline)                                             |
| PRINTER_DOUBLE_HEIGHT    | Optional | All          | False   | Print text double height                                                                                       |
| PRINTER_DOUBLR_WIDTH     | Optional | All          | False   | Print text double width                                                                                        |
| PRINTER_INVERSE          | Optional | All          | False   | Print 'upside down' mode                                                                                       |
| PRINTER_FLIP             | Optional | All          | False   | Print 'right - to - left' mode                                                                                 |
| LOG_LEVEL                | Optional | All          | INFO    | 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'                                                                |
|                          |          |              |         |                                                                                                                |

## API Endpoints

- `/`
  - Type: `GET`
  - Description: Health check endpoint. Returns a simple JSON message indicating the service is running.
  - Response Example:

    ```json
    {
      "message": "Printer API is running.",
      "printer_status": "online"
    }
    ```

- `/config/`
  - Type: `GET`
  - Description: Returns the current printer configuration from environment variables.
  - Response Example:

    ```json
    {
      "printer_type": "dummy"
    }
    ```

- `/print/`
  - Type: `POST`
  - Description: Print plain text or QR code. Accepts query parameters.
  - Parameters:
    - `content` (string) — Text or QR payload to print (required).
    - `copies` (int, >=1) — Number of copies to print (default: `1`).
    - `cut` (bool) — Cut paper after each copy (default: `True`).
    - `alignment` (string, 'left', 'center', 'right') — Text alignment (default: from env).
    - `qr` (bool) — If `True`, prints a QR code instead of text (default: `False`).
    - `size` (int, 1-16) — Font/QR size (default: `8`; used for QR codes ONLY).
  - Response Example:

    ```json
    {
      "message": "Content printeds."
    }
    ```

- `/barcode/`
  - Type: `POST`
  - Description: Print a Barcode code. Accepts query parameters.
  - Parameters:
    - `code` (string) — Text payload to print as barcode (required).
    - `type` (string) — Barcode type (e.g., `CODE39`, `EAN13`) (required).
    - `height` (int, 1-255) — Height of the barcode (default: `64`).
    - `width` (int, 2-6) — Width of the barcode (default: `3`).
    - `position` (string, 'none', 'above', 'below', 'both') — Text position (default: `below`).
    - `center` (bool) — Center the barcode (default: `True`).
    - `copies` (int, >=1) — Number of copies to print (default: `1`).
    - `cut` (bool) — Cut paper after each copy (default: `True`).
  - Response Example:

    ```json
    {
      "message": "Barcode printed."
    }
    ```

- `/image/`
  - Type: `POST`
  - Description: Print an image. Accepts multipart/form-data with an image file and query parameters.
  - Parameters:
    - `file` (file, type: image/png, image/jpg, image/bmp, image/gif) — Image file to print (required).
    - `high_density_vertical` (bool) — Use high density vertical mode (default: `True`).
    - `high_density_horizontal` (bool) — Use high density horizontal mode (default: `True`).
    - `impl` (string, 'bitImageColumn', 'bitImageRaster', 'graphics') — Image printing implementation (default: `bitImageRaster`).
    - `center` (bool) — Center the image (default: `True`).
    - `copies` (int, >=1) — Number of copies to print (default: `1`).
    - `cut` (bool) — Cut paper after each copy (default: `True`).
  - Response Example:

    ```json
    {
      "message": "Image printed."
    }
    ```

- `/cut/`
  - Type: `POST`
  - Description: Cut the paper.
  - Response Example:

    ```json
    {
      "message": "Paper cut."
    }
    ```

- `/docs`
  - Type: `GET`
  - Description: Access the interactive API documentation (Swagger UI).

## Examples

Using `curl` (POST with query string):

```bash
curl -X POST "http://localhost:8000/print/?content=Hello%20Printer&copies=1&cut=true"

curl -X POST "http://localhost:8000/print/?content=https%3A%2F%2Fexample.com&size=4&copies=1&cut=true&qr=true"
```

Using Python `requests`:

```python
import requests

base = "http://localhost:8000"

# Print text
payload = {"content": "Hello from API", "copies": 1, "cut": True}
resp = requests.post(f"{base}/print/", params=payload)
print(resp.status_code, resp.json())

# Print QR
payload = {"content": "https://example.com", "size": 4, "copies": 1, "cut": True, "qr": True}
resp = requests.post(f"{base}/print/", params=payload)
print(resp.status_code, resp.json())
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.
