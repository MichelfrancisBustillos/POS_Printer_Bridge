"""
Custom types for POS Printer Bridge
"""
# pylint: disable=C0103,

from enum import Enum
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
