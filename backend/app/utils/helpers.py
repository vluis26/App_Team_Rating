import logging
from app.services.ticketmaster_service import search_events
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

def fetch_and_assign_events(rating):
    """
    Fetch events based on the rating's city and assign them to the rating.

    Args:
        rating (RestaurantRatingModel): The restaurant rating instance.

    Returns:
        None
    """
    try:
        events = search_events(city=rating.city, max_events=3, classificationName='Music')
        rating.events = events
        logging.debug(f"Fetched Events for rating ID {rating.id}: {events}")
    except Exception as e:
        logging.error(f"Error fetching events for rating ID {rating.id}: {e}")
        rating.events = []
