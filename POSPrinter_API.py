from escpos.printer import Network
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import ipaddress

class Payload(BaseModel):
    content: str
    copies: int = 1
    size: int = 8
    cut: bool = True

class Printer(BaseModel):
    name: str
    ip: ipaddress.IPv4Address
    profile: str


app = FastAPI()
global printers 
printers = [Printer]

@app.get("/")
async def root():
    return {"message": "Printer API is running"}

@app.post("/initialize/")
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

@app.get("/printers", response_model=Printer)
def get_printers() -> Any:
    return printers

@app.post("/print_text/")
def print_text(id: int, payload: Payload):
    if not printers[id]:
        return {"error": "Printer not initialized"}
    for _ in range(payload.copies):
        printers[id].text(payload.content + "\n")
        if payload.cut:
            printers[id].cut()
    return {"status": "Text printed"}

@app.post("/print_qr/")
def print_qr(id: int, payload: Payload):
    if not printers[id]:
        return {"error": "Printer not initialized"}
    if not 1 <= payload.size <= 16:
        return {"error": "Inavlid size"}
    for _ in range(payload.copies):
        printers[id].qr(payload.content, size=payload.size)
        if payload.cut:
            printers[id].cut()
    return {"status": "QR code printed"}