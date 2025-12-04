from escpos.printer import Network as NetworkPrinter
from fastapi import FastAPI, Query, status
from pydantic import BaseModel, Field, create_model, ConfigDict
from pydantic.dataclasses import dataclass
from typing import Any, Annotated
import ipaddress

@dataclass
class Network:
    def __init__(self, ip, profile_name) -> None:
        self.ip = ip
        self.profile_name = profile_name
        self.printer = NetworkPrinter(ip, profile=profile_name)
        
    __pydantic_model__ = create_model("Network", x=(int, ...))
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
    ip: ipaddress.IPv4Address = Field(description="Printer IPv4 Address", title="IP Address")
    profile: str | None = Field(description="ESC/POS Printer Profile", title="Printer Profile")
    unit: Network | None
    
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

app = FastAPI()
global printers 
printers = []

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
        new_printer.unit = Network(ip_clean, new_printer.profile)
        printers.append(new_printer)
    else:
        new_printer.unit = Network(ip_clean)
        printers.append(new_printer)
    message = "Printer ID ", len(printers), " added"
    return {"status": message}

@app.get("/printers", status_code=200)
def get_printers() -> Any:
    return printers

@app.post("/print_text/", status_code=200)
def print_text(id: int,
               payload: Annotated[Payload, Query()]):
    if not printers[id].unit:
        return {"error": "Printer not initialized"}
    for _ in range(payload.copies):
        printers[id].content(payload.content + "\n")
        if payload.cut:
            printers[id].cut()
    return {"status": "Text printed"}

@app.post("/print_qr/", status_code=200)
def print_qr(id: int,
             payload: Annotated[Payload, Query()]):
    if not printers[id].unit:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    for _ in range(payload.copies):
        printers[id].qr(payload.content, size=payload.size)
        if payload.cut:
            printers[id].cut()
    return {"status": "QR code printed"}