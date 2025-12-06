"""
POS Printer API using FastAPI
"""
# pylint: disable=W0603,C0103

from typing import Any, Annotated
import logging
import os
import escpos.printer
import escpos.exceptions
from fastapi import FastAPI, Query, Response, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
from dotenv import load_dotenv
from customtypes import Alignments
from models import Payload, Barcode, ImageSettings

match os.getenv('LOG_LEVEL', 'INFO').upper():
    case 'DEBUG':
        user_log_level = logging.DEBUG
    case 'INFO':
        user_log_level = logging.INFO
    case 'WARNING':
        user_log_level = logging.WARNING
    case 'ERROR':
        user_log_level = logging.ERROR
    case 'CRITICAL':
        user_log_level = logging.CRITICAL
    case _:
        user_log_level = logging.INFO
logging.basicConfig(
    level=user_log_level,
    format="%(levelname)s: %(message)s",
)

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/", status_code=200)
async def root(response: Response) -> Any:
    """
    Root Endpoint
    """
    logging.info("Root endpoint called")
    if check_printer_initialized():
        logging.info("Printer status: online")
        return {"message": "Printer API is running", "printer_status": "online"}
    else:
        response.status_code = 400
        logging.warning("Printer not initialized")
        return {"message": "Printer API is running, but no printer is initialized"}

def check_printer_initialized() -> bool:
    """
    Check if the printer is initialized
    """
    if PRINTER is None:
        logging.error("Printer not initialized")
        return False
    elif PRINTER.is_online():
        logging.info("Printer is online")
        return True
    else:
        logging.warning("Printer is offline")
        return False

@app.get("/config", status_code=200)
def get_config() -> Any:
    """
    Docstring for get_config

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
def print_text(payload: Annotated[Payload, Query()], response: Response) -> Any:
    """
    Docstring for print_text
    
    :param payload: Description
    :type payload: Annotated[Payload, Query()]
    """
    if not check_printer_initialized():
        response.status_code = 400
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
    PRINTER.set(align=os.getenv('PRINTER_ALIGNMENT', 'left'))
    return {"status": "Content Printed"}

@app.post("/barcode/", status_code=200)
def print_barcode(barcode: Annotated[Barcode, Query()], response: Response) -> Any:
    """
    Print a barcode
    """
    if not check_printer_initialized():
        response.status_code = 400
        return {"error": "Printer not initialized"}
    logging.info("Barcode type: %s", barcode.type.value)
    try:
        for _ in range(barcode.copies):
            logging.info("Printing barcode...")
            PRINTER.barcode(barcode.code,
                            barcode.type.value,
                            height=barcode.height,
                            width=barcode.width,
                            align_ct=barcode.center)
            if barcode.cut:
                logging.info("Cutting...")
                PRINTER.cut()
    except (escpos.exceptions.BarcodeCodeError,
            escpos.exceptions.BarcodeSizeError,
            escpos.exceptions.BarcodeTypeError) as e:
        logging.error("Barcode printing error: %s", str(e))
        response.status_code = 400
        return {"error": f"Barcode printing error: {str(e)}"}
    return {"status": "Barcode Printed"}

@app.post("/image/", status_code=200)
def print_image(file: UploadFile,
                imagesettings: Annotated[ImageSettings, Query()],
                response: Response) -> Any:
    """
    Print an image
    """
    if not check_printer_initialized():
        response.status_code = 400
        return {"error": "Printer not initialized"}
    if not file:
        response.status_code = 400
        return {"error": "No image file provided"}
    if file.content_type not in ["image/png", "image/gif", "image/bmp", "image/jpg"]:
        response.status_code = 400
        return {"error": "Unsupported image format. Supported formats are PNG, JPG, BMP, GIF."}
    image = Image.open(file.file)
    try:
        for _ in range(imagesettings.copies):
            logging.info("Printing image...")
            PRINTER.image(image,
                          high_density_vertical=imagesettings.high_density_vertical,
                          high_density_horizontal=imagesettings.high_density_horizontal,
                          impl=imagesettings.impl.value,
                          center=imagesettings.center)
            if imagesettings.cut:
                logging.info("Cutting...")
                PRINTER.cut()
    except (escpos.exceptions.ImageWidthError, escpos.exceptions.ImageSizeError) as e:
        logging.error("Image printing error: %s", str(e))
        response.status_code = 400
        return {"error": f"Image printing error: {str(e)}"}
    return {"status": "Image Printed"}

@app.post("/cut/", status_code=200)
def cut_paper(response: Response) -> Any:
    """
    Cut the paper
    """
    if not check_printer_initialized():
        response.status_code = 400
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
            PRINTER = escpos.printer.Usb(vendor_id,
                                         product_id,
                                         interface=interface,
                                         endpoint_in=endpoint_in,
                                         endpoint_out=endpoint_out,
                                         profile=my_profile)
        case 'serial':
            serial_port = str(os.getenv('PRINTER_SERIAL_PORT'))
            baudrate = int(os.getenv('PRINTER_SERIAL_BAUDRATE', '9600'))
            bytesize = int(os.getenv('PRINTER_SERIAL_BYTESIZE', '8'))
            parity = os.getenv('PRINTER_SERIAL_PARITY', 'N')
            stopbits = int(os.getenv('PRINTER_SERIAL_STOPBITS', '1'))
            timeout = int(os.getenv('PRINTER_SERIAL_TIMEOUT', '1'))
            dsrdtr = os.getenv('PRINTER_SERIAL_DSRDTR', 'False') == 'True'
            rtscts = os.getenv('PRINTER_SERIAL_RTSCTS', 'False') == 'True'
            PRINTER = escpos.printer.Serial(devfile=serial_port,
                                            baudrate=baudrate,
                                            bytesize=bytesize,
                                            parity=parity,
                                            stopbits=stopbits,
                                            timeout=timeout,
                                            dsrdtr=dsrdtr,
                                            rtscts=rtscts,
                                            profile=my_profile)
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

    if check_printer_initialized():
        logging.info("Printer initialized")
    else:
        logging.error("Failed to initialize printer")
        raise SystemExit("Failed to initialize printer")

if __name__ == "__main__":
    PRINTER = escpos.printer.Dummy()
    env_path = os.path.dirname(os.getcwd()) + '/.env'
    if os.path.exists(env_path):
        logging.info("Loading .env file")
        load_dotenv(env_path)
    else:
        logging.info(".env file not found, using system environment variables")
    init_printer()

    uvicorn.run(app, host="0.0.0.0", port=8000)
