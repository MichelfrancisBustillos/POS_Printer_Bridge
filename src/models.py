"""
Models for POS Printer Bridge
"""
from pydantic import BaseModel, Field
from customtypes import Alignments, Positions, BarcodeTypes, ImplTypes

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
