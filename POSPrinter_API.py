from escpos.printer import Network
from fastapi import FastAPI, Query, status
from pydantic import BaseModel, Field
from typing import Any, Annotated
import ipaddress

class Payload(BaseModel):
    content: str = Field(description="Text or QR Code to Print", title="Content")
    copies: int = Field(ge=1, description="Number of Copies", title="Copies", default=1)
    size: int = Field(ge=1, le=16, description="Font size", title="Size", default=8)
    cut: bool = Field(description="Cut after each copy", title="Cut", default=True)

    model_config = {
        "json_scheme_extra": {
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
    name: str | None = Field(description="Printer Name", title="Name", default="My Printer")
    ip: ipaddress.IPv4Address = Field(description="Printer IPv4 Address", title="IP Address")
    profile: str | None = Field(description="ESC/POS Printer Profile", title="Printer Profile")

    model_config = {
        "json_scheme_extra": {
            "examples": [
                {
                    "name": "My Printer",
                    "ip": 192.168.1.2,
                    "profile": "TM-T88V",
                }
            ]
        }
    }


app = FastAPI()
global printers 
printers = [Printer]

@app.get("/", status_code=200)
async def root():
    return {"message": "Printer API is running"}

@app.post("/initialize/", status_code=status.HTTP_201_CREATED)
def initialize_printer(new_printer: Printer):
    try:
        ip_clean = ipaddress.ip_address(new_printer.ip)
    except ValueError:
        return {"status": "Invalid IP"}
    
    if new_printer.profile:
        printers.append(Network(ip_clean, profile=new_printer.profile))
    else:
        printers.append(Network(ip_clean))
    message = "Printer ID ", len(printers), " added"
    return {"status": message}

@app.get("/printers", response_model=Printer, status_code=200)
def get_printers() -> Any:
    return printers

@app.post("/print_text/", status_code=200)
def print_text(id: int,
               payload: Annotated[Payload, Query()]):
    if not printers[id]:
        return {"error": "Printer not initialized"}
    for _ in range(payload.copies):
        printers[id].text(payload.content + "\n")
        if payload.cut:
            printers[id].cut()
    return {"status": "Text printed"}

@app.post("/print_qr/", status_code=200)
def print_qr(id: int,
             payload: Annotated[Payload, Query()]):
    if not printers[id]:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    for _ in range(payload.copies):
        printers[id].qr(payload.content, size=payload.size)
        if payload.cut:
            printers[id].cut()
    return {"status": "QR code printed"}