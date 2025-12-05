"""
Module for functional tests of the POS Printer Bridge API.
"""
import requests
import pytest

def test_root():
    """
    Docstring for test_root
    """
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200

def test_get_config():
    """
    Docstring for test_get_config
    """
    response = requests.get("http://localhost:8000/config")
    assert response.status_code == 200

def test_print_text():
    """
    Docstring for test_print_text
    """
    payload = {
        "content": "Test Print",
        "copies": 1,
        "cut": True
    }
    response = requests.post("http://localhost:8000/print_text/", params=payload)
    assert response.status_code == 200

def test_print_qr():
    """
    Docstring for test_print_qr
    """
    payload = {
        "content": "https://example.com",
        "size": 4,
        "copies": 1,
        "cut": True
    }
    response = requests.post("http://localhost:8000/print_qr/", params=payload)
    assert response.status_code == 200
