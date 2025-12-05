from escpos.printer import Network
from fastapi import FastAPI, Query, status
from pydantic import BaseModel, Field, create_model, ConfigDict
from pydantic.dataclasses import dataclass
from typing import Any, Annotated
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

app = FastAPI()

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

    return {"status": "Printer Initialized"}

@app.get("/printer", status_code=200)
def get_printers() -> Any:
    return printer

@app.post("/print_text/", status_code=200)
def print_text(payload: Annotated[Payload, Query()]):
    global printer
    if not printer:
        return {"error": "Printer not initialized"}
    for _ in range(payload.copies):
        printer.text(payload.content + "\n")
        if payload.cut:
            printer.cut()
    return {"status": "Text printed"}

@app.post("/print_qr/", status_code=200)
def print_qr(payload: Annotated[Payload, Query()]):
    global printer
    if not printer:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    for _ in range(payload.copies):
        printer.qr(payload.content, size=payload.size)
        if payload.cut:
            printer.cut()
    return {"status": "QR code printed"}