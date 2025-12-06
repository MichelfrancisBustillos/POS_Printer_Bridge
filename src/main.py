"""
POS Printer API using FastAPI
"""
# pylint: disable=W0603,C0103

from typing import Any, Annotated
import logging
import os
import escpos.printer
import escpos.exceptions
import escpos.capabilities
import serial.serialutil
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

    response.status_code = 400
    logging.warning("Printer not initialized")
    return {"message": "Printer API is running, but no printer is initialized"}

def check_printer_initialized() -> bool:
    """
    Check if the printer is initialized
    """
    try:
        PRINTER.is_online()
        logging.info("Printer is online")
        return True
    except NotImplementedError:
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
            center = bool(payload.alignment == Alignments.CENTER)
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

    match os.getenv('PRINTER_TYPE'):
        case 'network':
            try:
                PRINTER = escpos.printer.Network(os.getenv('PRINTER_IP'),
                                                 profile=os.getenv('PRINTER_PROFILE', None))
            except ConnectionRefusedError as e:
                logging.error("Network printer connection error: %s", str(e))
        case 'usb':
            try:
                PRINTER = escpos.printer.Usb(os.getenv('PRINTER_USB_VENDOR_ID'),
                                            os.getenv('PRINTER_USB_PRODUCT_ID'),
                                            interface=os.getenv('PRINTER_USB_INTERFACE',
                                                                None),
                                            endpoint_in=os.getenv('PRINTER_USB_ENDPOINT_IN',
                                                                  None),
                                            endpoint_out=os.getenv('PRINTER_USB_ENDPOINT_OUT',
                                                                   None),
                                            profile=os.getenv('PRINTER_PROFILE', None))
            except escpos.exceptions.USBNotFoundError as e:
                logging.error(str(e))
        case 'serial':
            try:
                PRINTER = escpos.printer.Serial(devfile=str(os.getenv('PRINTER_SERIAL_PORT')),
                                                baudrate=int(os.getenv('PRINTER_SERIAL_BAUDRATE',
                                                                       '9600')),
                                                bytesize=int(os.getenv('PRINTER_SERIAL_BYTESIZE',
                                                                       '8')),
                                                parity=os.getenv('PRINTER_SERIAL_PARITY',
                                                                 'N'),
                                                stopbits=int(os.getenv('PRINTER_SERIAL_STOPBITS',
                                                                       '1')),
                                                timeout=int(os.getenv('PRINTER_SERIAL_TIMEOUT',
                                                                      '1')),
                                                dsrdtr=os.getenv('PRINTER_SERIAL_DSRDTR',
                                                                'False') == 'True',
                                                rtscts=os.getenv('PRINTER_SERIAL_RTSCTS',
                                                                'False') == 'True',
                                                profile=os.getenv('PRINTER_PROFILE', None))
            except serial.serialutil.SerialException as e:
                logging.error(str(e))
        case _:
            logging.error("Unsupported or undefined PRINTER_TYPE")
            raise SystemExit("Unsupported or undefined PRINTER_TYPE")

    if check_printer_initialized():
        logging.info("Printer initialized")
    else:
        logging.error("Failed to initialize printer")

    try:
        logging.info("Setting default printer configurations")
        PRINTER.set(
            align=Alignments(os.getenv('PRINTER_ALIGNMENT', 'left')),
            font=os.getenv('PRINTER_FONT', 'a').lower(),
            bold=bool(os.getenv('PRINTER_BOLD', 'False')),
            underline=int(os.getenv('PRINTER_UNDERLINE', '0')),
            width=1,
            height=1,
            density=9,
            invert=bool(os.getenv('PRINTER_INVERSE', 'False')),
            flip=bool(os.getenv('PRINTER_FLIP', 'False')),
            double_height=bool(os.getenv('PRINTER_DOUBLE_HEIGHT', 'False')),
            double_width=bool(os.getenv('PRINTER_DOUBLE_WIDTH', 'False')),
            custom_size=False
        )
    except escpos.capabilities.NotSupported as e:
        logging.warning(str(e))

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
