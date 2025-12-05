from escpos.printer import Network
from fastapi import FastAPI, Query, status
import uvicorn
from pydantic import BaseModel, Field, create_model, ConfigDict
from pydantic.dataclasses import dataclass
import configparser
from typing import Any, Annotated
import logging
import os
import ipaddress

class Payload(BaseModel):
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
    return {"message": "Printer API is running"}

@app.post("/initialize/", status_code=status.HTTP_201_CREATED)
def initialize_printer(new_printer: Printer):
    global printer
    if new_printer.profile:
        printer = Network(new_printer.ip, profile=new_printer.profile)
    else:
        printer = Network(new_printer.ip)
        
    config = configparser.ConfigParser()
    config.add_section("Printer")
    config.set("Printer", "Name", new_printer.name)
    config.set("Printer", "IP", new_printer.ip)
    if new_printer.profile:
        config.set("Printer", "Profile", new_printer.profile)
    with open("printer.ini", 'w') as configfile:
        config.write(configfile)

    return {"status": "Printer Initialized"}

@app.get("/config", status_code=200)
def get_printers() -> Any:
    logging.info("Returning Config")
    if os.path.exists('printer.ini'):
        config = configparser.ConfigParser()
        config.read('printer.ini')
        logging.info(config.items('Printer'))
        return config.items('Printer')
    else:
        logging.error("No Config file found")
        return {"stats": "No config file found"}

@app.post("/print_text/", status_code=200)
def print_text(payload: Annotated[Payload, Query()]):
    global printer
    if not printer:
        return {"error": "Printer not initialized"}
    logging.info(f"Printing {payload.content} {payload.copies} times.")
    for _ in range(payload.copies):
        printer.text(payload.content + "\n")
        if payload.cut:
            logging.info("Cutting...")
            printer.cut()
    return {"status": "Text printed"}

@app.post("/print_qr/", status_code=200)
def print_qr(payload: Annotated[Payload, Query()]):
    global printer
    if not printer:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    logging.info(f"Printing QR Code {payload.copies} times.")
    for _ in range(payload.copies):
        printer.qr(payload.content, size=payload.size)
        if payload.cut:
            logging.info("Cutting...")
            printer.cut()
    return {"status": "QR code printed"}

if __name__ == "__main__":
    if os.path.exists('printer.ini'):
        config = configparser.ConfigParser()
        logger.info("Initializing Printer from File")
        config.read('printer.ini')
        name = config.get('Printer', 'Name')
        ip = config.get('Printer', 'IP')
        my_profile = config.get('Printer', 'Profile')
        global printer
        if my_profile:
            printer = Network(ip, profile=my_profile)
        else:
            printer = Network(ip)
            
    uvicorn.run(app, host="0.0.0.0", port=8000)