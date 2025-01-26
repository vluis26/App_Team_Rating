import logging
import requests
import os

def extract_city(address):
    """
    Extracts the city from a given address string.

    Args:
        address (str): The full address string.

    Returns:
        str or None: The extracted city or None if extraction fails.
    """
    try:
        # Split the address by commas
        parts = address.split(',')
        # Assuming the city is the second part
        if len(parts) < 2:
            logging.error("Address does not contain enough parts to extract city.")
            return None
        city = parts[1].strip()
        return city
    except Exception as e:
        logging.error(f"Error extracting city: {e}")
        return None
