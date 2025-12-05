"""
POS Printer API using FastAPI"""
from typing import Any, Annotated
import logging
import os
from escpos.printer import Network
from fastapi import FastAPI, Query
import uvicorn
from pydantic import BaseModel, Field, create_model, ConfigDict
from pydantic.dataclasses import dataclass
from dotenv import load_dotenv

class Payload(BaseModel):
    """
    Payload Model for Printing Text or QR Code
    """
    content: str = Field(description="Text or QR Code to Print", title="Content")
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    size: int = Field(ge=1, le=16, description="Font size", title="Size", default=8)
    cut: bool = Field(description="Cut after each copy", title="Cut", default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Content to print",
                    "copies": 1,
                    "size": 8,
                    "cut": True,
                }
            ]
        }
    }

class Printer(BaseModel):
    """
    Printer Model for Configuration
    """
    name: str | None = Field(description="Printer Name", title="Name")
    ip: str = Field(description="Printer IPv4 Address", title="IP Address")
    profile: str | None = Field(description="ESC/POS Printer Profile", title="Printer Profile")

    model_config = ConfigDict(
        arbitrary_types_allowed = True,
        json_schema_extra = {
            "examples": [
                {
                    "name": "My Printer",
                    "ip": "192.168.1.2",
                    "profile": "TM-T88V",
                }
            ]
        }
    )

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
    return {"message": "Printer API is running"}

@app.get("/config", status_code=200)
def get_printers() -> Any:
    """
    Docstring for get_printers
    
    :return: Description
    :rtype: Any
    """
    ip = os.getenv('PRINTER_IP')
    my_profile = os.getenv('PRINTER_PROFILE')
    logging.info("Returning Config")
    logging.info("IP: %s, Profile: %s", ip, my_profile)
    return ({
        "ip": ip,
        "profile": my_profile,
    })

@app.post("/print_text/", status_code=200)
def print_text(payload: Annotated[Payload, Query()]):
    """
    Docstring for print_text
    
    :param payload: Description
    :type payload: Annotated[Payload, Query()]
    """
    if not PRINTER:
        return {"error": "Printer not initialized"}
    logging.info("Printing %s %s times.", payload.content, payload.copies)
    for _ in range(payload.copies):
        PRINTER.text(payload.content + "\n")
        if payload.cut:
            logging.info("Cutting...")
            PRINTER.cut()
    return {"status": "Text printed"}

@app.post("/print_qr/", status_code=200)
def print_qr(payload: Annotated[Payload, Query()]):
    """
    Docstring for print_qr
    
    :param payload: Description
    :type payload: Annotated[Payload, Query()]
    """
    if not PRINTER:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    logging.info("Printing QR Code %s times.", payload.copies)
    for _ in range(payload.copies):
        PRINTER.qr(payload.content, size=payload.size)
        if payload.cut:
            logging.info("Cutting...")
            PRINTER.cut()
    return {"status": "QR code printed"}

def init_printer():
    """
    Initialize the printer from environment variables
    """
    global PRINTER
    ip = os.getenv('PRINTER_IP')
    my_profile = os.getenv('PRINTER_PROFILE')
    if my_profile:
        PRINTER = Network(ip, profile=my_profile)
    else:
        PRINTER = Network(ip)

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
