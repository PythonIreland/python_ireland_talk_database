"""
Meetup API scraper for Python Ireland Talk Database

Uses Meetup GraphQL API to fetch event data
API Endpoint: https://www.meetup.com/gql
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MeetupVenue:
    name: str = ""
    city: str = ""
    address: str = ""


@dataclass
class MeetupHost:
    name: str = ""


@dataclass
class MeetupEvent:
    id: str
    title: str
    description: str = ""
    event_url: str = ""
    start_time: str = ""
    end_time: str = ""
    going_count: int = 0
    venue: Optional[MeetupVenue] = None
    hosts: List[MeetupHost] = None
    topics: List[str] = None
    group_name: str = ""

    def __post_init__(self):
        if self.hosts is None:
            self.hosts = []
        if self.topics is None:
            self.topics = []
        if self.venue is None:
            self.venue = MeetupVenue()


class Meetup:
    """Clean Meetup GraphQL API scraper"""

    DEFAULT_GROUPS = {
        "pythonireland": "Python Ireland",
        "dublin-python": "Dublin Python",
        "cork-python-meetup": "Cork Python Meetup",
    }

    def __init__(self, groups: Optional[Dict[str, str]] = None):
        self.groups = groups or self.DEFAULT_GROUPS
        self.api_url = "https://www.meetup.com/gql"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; PythonIrelandTalkDB/1.0)",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def get_all_data(self) -> List[MeetupEvent]:
        """Get all events from all configured groups"""
        all_events = []

        for group_urlname, group_display_name in self.groups.items():
            logger.info(f"Fetching events for {group_display_name} ({group_urlname})")

            try:
                events = self._get_group_events(group_urlname, group_display_name)
                all_events.extend(events)
                logger.info(f"Found {len(events)} events for {group_display_name}")

            except Exception as e:
                logger.error(f"Failed to fetch events for {group_display_name}: {e}")
                continue

        logger.info(f"Total events found: {len(all_events)}")
        return all_events

    def _get_group_events(
        self, group_urlname: str, group_display_name: str
    ) -> List[MeetupEvent]:
        """Fetch events for a specific group"""
        query = """
        query ($urlname: String!) {
            groupByUrlname(urlname: $urlname) {
                id
                name
                pastEvents(input: { first: 100 }) {
                    edges {
                        node {
                            id
                            title
                            dateTime
                            endTime
                            description
                            going
                            eventUrl
                            venue {
                                name
                                city
                                address
                            }
                            hosts {
                                name
                            }
                            topics {
                                edges {
                                    node {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        payload = {"query": query, "variables": {"urlname": group_urlname}}

        try:
            response = self.session.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors for {group_urlname}: {data['errors']}")
                return []

            if not data.get("data", {}).get("groupByUrlname"):
                logger.warning(f"No group data found for {group_urlname}")
                return []

            events_data = data["data"]["groupByUrlname"]["pastEvents"]["edges"]
            events = []

            for edge in events_data:
                event = self._parse_event(edge["node"], group_display_name)
                if event:
                    events.append(event)

            return events

        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {group_urlname}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse response for {group_urlname}: {e}")
            return []

    def _parse_event(self, event_data: dict, group_name: str) -> Optional[MeetupEvent]:
        """Parse a single event from GraphQL response"""
        try:
            event_id = event_data.get("id", "")
            if not event_id:
                return None

            # Parse venue
            venue_data = event_data.get("venue")
            venue = MeetupVenue()
            if venue_data:
                venue = MeetupVenue(
                    name=venue_data.get("name", ""),
                    city=venue_data.get("city", ""),
                    address=venue_data.get("address", ""),
                )

            # Parse hosts
            hosts_data = event_data.get("hosts", [])
            hosts = [MeetupHost(name=host.get("name", "")) for host in hosts_data]

            # Parse topics
            topics_data = event_data.get("topics", {}).get("edges", [])
            topics = [
                topic["node"]["name"]
                for topic in topics_data
                if topic.get("node", {}).get("name")
            ]

            # Clean description (remove HTML tags if present)
            description = event_data.get("description", "")
            if description:
                # Basic HTML tag removal
                import re

                description = re.sub(r"<[^>]+>", "", description).strip()

            return MeetupEvent(
                id=event_id,
                title=event_data.get("title", ""),
                description=description,
                event_url=event_data.get("eventUrl", ""),
                start_time=event_data.get("dateTime", ""),
                end_time=event_data.get("endTime", ""),
                going_count=event_data.get("going", 0),
                venue=venue,
                hosts=hosts,
                topics=topics,
                group_name=group_name,
            )

        except Exception as e:
            logger.warning(
                f"Failed to parse event {event_data.get('id', 'unknown')}: {e}"
            )
            return None


# For testing and CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Meetup data")
    parser.add_argument("--group", type=str, help="Meetup group URL name")
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )

    args = parser.parse_args()

    groups = None
    if args.group:
        groups = {args.group: args.group}

    scraper = Meetup(groups=groups)
    events = scraper.get_all_data()

    if args.output == "json":
        import json

        print(json.dumps([event.__dict__ for event in events], indent=2, default=str))
    else:
        print(f"Found {len(events)} events")
        for event in events[:5]:  # Show first 5
            print(
                f"- {event.title} ({event.group_name}) - {len(event.hosts)} hosts, {event.going_count} attendees"
            )
