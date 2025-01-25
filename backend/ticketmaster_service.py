import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load the API key from environment variables
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY')
BASE_URL = 'https://app.ticketmaster.com/discovery/v2/'


def search_events(city, max_events=3, classificationName=None):
    """
    Search for events in a specific city using the Ticketmaster API.

    Args:
        city (str): The city to search events in.
        max_events (int): Maximum number of events to retrieve.
        classificationName (str, optional): Type of events to filter (e.g., Music, Sports).

    Returns:
        list: A list of event dictionaries.

    Raises:
        Exception: If the API request fails.
    """
    endpoint = f"{BASE_URL}events.json"
    params = {
        'apikey': TICKETMASTER_API_KEY,
        'city': city,
        'size': max_events,
        'sort': 'date,asc',  # Sort by upcoming events
    }

    if classificationName:
        params['classificationName'] = classificationName

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses
        data = response.json()
        events = data.get('_embedded', {}).get('events', [])
        logging.debug(f"Fetched {len(events)} events for city: {city}")
        return events[:max_events]
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"Ticketmaster API HTTP error: {http_err}")
    except Exception as err:
        logging.error(f"Error fetching events: {err}")
        raise Exception(f"An error occurred while fetching events: {err}")


def get_event_details(event_id):
    """
    Retrieve detailed information about a specific event.

    Args:
        event_id (str): The ID of the event to retrieve.

    Returns:
        dict: A dictionary containing event details.

    Raises:
        Exception: If the API request fails.
    """
    endpoint = f"{BASE_URL}events/{event_id}.json"
    params = {
        'apikey': TICKETMASTER_API_KEY
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        event_details = response.json()
        logging.debug(f"Fetched details for event ID: {event_id}")
        return event_details
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"Ticketmaster API HTTP error: {http_err}")
    except Exception as err:
        logging.error(f"Error fetching event details: {err}")
        raise Exception(f"An error occurred while fetching event details: {err}")
