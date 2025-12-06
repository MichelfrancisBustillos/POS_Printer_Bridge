"""
POS Printer API using FastAPI
"""
# pylint: disable=C0103,W0603

from typing import Any, Annotated
from enum import Enum
import logging
import os
import escpos.printer
import escpos.exceptions
from fastapi import FastAPI, Query, Response, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv

class Alignments(str, Enum):
    """
    Docstring for Alignments
    """
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'

class Positions(str, Enum):
    """
    Docstring for Positions
    """
    ABOVE = 'above'
    BELOW = 'below'
    BOTH = 'both'
    NONE = 'none'

class BarcodeTypes(str, Enum):
    """
    Docstring for BarcodeTypes
    """
    UPC_A = 'UPC-A'
    UPC_E = 'UPC-E'
    EAN13 = 'EAN13'
    EAN8 = 'EAN8'
    CODE39 = 'CODE39'
    ITF = 'ITF'
    NW7 = 'NW7'

class ImplTypes(str, Enum):
    """
    Docstring for ImplTypes
    """
    bitImageRaster = 'bitImageRaster'
    graphics = 'graphics'
    bitImageColumn = 'bitImageColumn'
class Payload(BaseModel):
    """
    Payload Model for Printing Text or QR Code
    """
    content: str = Field(description="Content to Print", title="Content")
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    cut: bool = Field(description="Cut after each copy", title="Cut", default=True)
    alignment : Alignments = Field(description="Alignment of the output",
                                   title="Alignment",
                                   default=Alignments.LEFT)
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

class Barcode(BaseModel):
    """
    Barcode Model
    """
    code: str = Field(description="Barcode Content", title="Code")
    type: BarcodeTypes = Field(description="Barcode Type", title="Type")
    height: int = Field(ge=1, le=255,
                        description="Height of the Barcode",
                        title="Height", default=64)
    width: int = Field(ge=2, le=6, description="Width of the Barcode", title="Width", default=3)
    position: Positions = Field(description="Position of the Human Readable Text",
                                title="Position",
                                default=Positions.BELOW)
    center: bool = Field(description="Center the Barcode", title="Center", default=False)
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    cut:  bool = Field(description="Cut after printing the barcode", title="Cut", default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "123456789012",
                    "type": "EAN13",
                    "height": 64,
                    "width": 3,
                    "position": "below",
                    "center": False,
                    "copies": 1,
                    "cut": True
                }
            ]
        }
    }

class ImageSettings(BaseModel):
    """
    Image Settings Model
    """
    high_density_vertical: bool = Field(description="High Density Vertical",
                                        title="High Density Vertical",
                                        default=True)
    high_density_horizontal: bool = Field(description="High Density Horizontal",
                                          title="High Density Horizontal", default=True)
    impl: ImplTypes = Field(description="Implementation Type", title="Implementation",
                            default=ImplTypes.bitImageRaster)
    center: bool = Field(description="Center the Image", title="Center", default=False)
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    cut: bool = Field(description="Cut after printing the image", title="Cut", default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "high_density_vertical": True,
                    "high_density_horizontal": True,
                    "impl": "bitImageRaster",
                    "center": False,
                    "copies": 1,
                    "cut": True
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
    PRINTER.set(align=os.getenv('PRINTER_ALIGNMENT', 'left'))
    return {"status": "Content Printed"}

@app.post("/barcode/", status_code=200)
def print_barcode(barcode: Annotated[Barcode, Query()], response: Response):
    """
    Print a barcode
    """
    if not PRINTER:
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
                response: Response):
    """
    Print an image
    """
    if not PRINTER:
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
