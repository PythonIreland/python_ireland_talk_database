import sys
import os

from lib.engine.sessionize import Sessionize


def main():
    print("Fetching Sessionize data for PyCon events...")

    # You can expand this list with more PyCon event IDs as you find them
    pycon_events = {
        "amtv2kwb": "PyCon Ireland 2022",
        "jb4vxosa": "PyCon Limerick 2023",
        "jbshwhme": "PyCon Ireland 2023",
        # Add more event IDs here as you discover them
    }

    sessionize_scraper = Sessionize(events=pycon_events)
    data = sessionize_scraper.get_all_data()

    print(f"Found {len(data)} talks across {len(pycon_events)} events.")
    print("First Talk Details:")
    if data:
        first_talk = data[0]
        print(f"Title: {first_talk.title}")
        print(f"Speaker: {first_talk.speakers}")
        print(f"Event: {first_talk.event_name}")
        print(f"Description: {first_talk.description[:100]}...")


def test_event_patterns():
    """Try some common event ID patterns to find more PyCon events"""
    import requests

    # These are just examples - you'd need to find actual event IDs
    potential_ids = [
        # Add any other event IDs you want to test
    ]

    for event_id in potential_ids:
        url = f"https://sessionize.com/api/v2/{event_id}/view/Sessions?under=True"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and "PyCon" in response.text:
                print(f"Found potential PyCon event: {event_id}")
        except:
            pass


if __name__ == "__main__":
    main()
