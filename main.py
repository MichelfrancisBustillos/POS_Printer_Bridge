"""
POS Printer API using FastAPI
"""
from typing import Any, Annotated
from enum import Enum
import logging
import os
import escpos.printer
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

class Alignments(str, Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'

class Payload(BaseModel):
    """
    Payload Model for Printing Text or QR Code
    """
    content: str = Field(description="Content to Print", title="Content")
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    cut: bool = Field(description="Cut after each copy", title="Cut", default=True)
    alignment : Alignments = Field(description="Alignment of the output", title="Alignment", default=Alignments.LEFT)
    qr: bool = Field(description="Print as QR Code", title="QR", default=False)
    size: int = Field(ge=1, le=16, description="Size of the QR Code", title="Size", default=8)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Content to print",
                    "copies": 1,
                    "cut": True,
                    "alignment": "left",
                    "qr": False,
                    "size": 8
                }
            ]
        }
    }

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/", status_code=200)
async def root():
    """
    Root Endpoint
    """
    logging.info("Root endpoint called")
    if PRINTER:
        logging.info("Printer status: %s", PRINTER.is_online())
        return {"message": "Printer API is running", "printer_status": PRINTER.is_online()}
    else:
        logging.warning("Printer not initialized")
        return {"message": "Printer API is running, but no printer is initialized"}

@app.get("/config", status_code=200)
def get_printer() -> Any:
    """
    Docstring for get_printer

    :return: Description
    :rtype: Any
    """
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith('PRINTER_'):
            env_vars[key] = value
    logging.info("Current Environment Variables: %s", env_vars)
    return JSONResponse(content=env_vars)

@app.post("/print/", status_code=200)
def print_text(payload: Annotated[Payload, Query()]):
    """
    Docstring for print_text
    
    :param payload: Description
    :type payload: Annotated[Payload, Query()]
    """
    if not PRINTER:
        return {"error": "Printer not initialized"}
    logging.info("Setting alignment to %s", payload.alignment)
    PRINTER.set(align=payload.alignment)
    logging.info("Printing...")
    for _ in range(payload.copies):
        if not payload.qr:
            PRINTER.text(payload.content + "\n")
        else:
            if payload.alignment == Alignments.CENTER:
                center = True
            else:
                center = False
            PRINTER.qr(payload.content, size=payload.size, center=center)
        if payload.cut:
            logging.info("Cutting...")
            PRINTER.cut()
    PRINTER.set(align=os.getenv('PRINTER_ALIGNMENT', 'left'))  # Reset alignment to left after printing
    return {"status": "Content Printed"}

@app.post("/cut/", status_code=200)
def cut_paper():
    """
    Cut the paper
    """
    if not PRINTER:
        return {"error": "Printer not initialized"}
    logging.info("Cutting paper...")
    PRINTER.cut()
    return {"status": "Paper Cut"}

def init_printer():
    """
    Initialize the printer from environment variables
    """
    global PRINTER
    if os.getenv('PRINTER_PROFILE'):
        logging.info("Using printer profile: %s", os.getenv('PRINTER_PROFILE'))
        my_profile = os.getenv('PRINTER_PROFILE')
    else:
        my_profile = None

    match os.getenv('PRINTER_TYPE'):
        case 'network':
            ip = os.getenv('PRINTER_IP')
            PRINTER = escpos.printer.Network(ip, profile=my_profile)
        case 'usb':
            vendor_id = os.getenv('PRINTER_USB_VENDOR_ID')
            product_id = os.getenv('PRINTER_USB_PRODUCT_ID')
            interface = os.getenv('PRINTER_USB_INTERFACE', None)
            endpoint_in = os.getenv('PRINTER_USB_ENDPOINT_IN', None)
            endpoint_out = os.getenv('PRINTER_USB_ENDPOINT_OUT', None)
            PRINTER = escpos.printer.Usb(vendor_id, product_id, interface=interface, endpoint_in=endpoint_in, endpoint_out=endpoint_out, profile=my_profile)
        case 'serial':
            serial_port = str(os.getenv('PRINTER_SERIAL_PORT'))
            baudrate = int(os.getenv('PRINTER_SERIAL_BAUDRATE', '9600'))
            bytesize = int(os.getenv('PRINTER_SERIAL_BYTESIZE', '8'))
            parity = os.getenv('PRINTER_SERIAL_PARITY', 'N')
            stopbits = int(os.getenv('PRINTER_SERIAL_STOPBITS', '1'))
            timeout = int(os.getenv('PRINTER_SERIAL_TIMEOUT', '1'))
            dsrdtr = os.getenv('PRINTER_SERIAL_DSRDTR', 'False') == 'True'
            rtscts = os.getenv('PRINTER_SERIAL_RTSCTS', 'False') == 'True'
            PRINTER = escpos.printer.Serial(devfile=serial_port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout, dsrdtr=dsrdtr, rtscts=rtscts, profile=my_profile)
        case _:
            logging.error("Unsupported or undefined PRINTER_TYPE")
            raise SystemExit("Unsupported or undefined PRINTER_TYPE")
        
    alignment = os.getenv('PRINTER_ALIGNMENT', 'left')
    font = os.getenv('PRINTER_FONT', 'a')
    bold = bool(os.getenv('PRINTER_BOLD', 'False'))
    underline = int(os.getenv('PRINTER_UNDERLINE', '0'))
    double_height = bool(os.getenv('PRINTER_DOUBLE_HEIGHT', 'False'))
    double_width = bool(os.getenv('PRINTER_DOUBLE_WIDTH', 'False'))
    inverse = bool(os.getenv('PRINTER_INVERSE', 'False'))
    flip = bool(os.getenv('PRINTER_FLIP', 'False'))
    PRINTER.set(
        align=alignment,
        font=font,
        bold=bold,
        underline=underline,
        width=1,
        height=1,
        density=9,
        invert=inverse,
        flip=flip,
        double_height=double_height,
        double_width=double_width,
        custom_size=False
    )
    logging.info("Printer initialized")

if __name__ == "__main__":
    PRINTER = None
    if os.path.exists('.env'):
        logging.info("Loading .env file")
        load_dotenv('.env')
        init_printer()
    else:
        logging.error("No .env file found. Printer not initialized.")
        raise SystemExit("No .env file found. Exiting.")

    uvicorn.run(app, host="0.0.0.0", port=8000)
