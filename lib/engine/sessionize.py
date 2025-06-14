"""
Sessionize API scraper for Python Ireland Talk Database

Uses publicly accessible Sessionize Embedding API: https://sessionize.com/playbook/embedding
API Endpoint: https://sessionize.com/api/v2/{event_id}/view/{type}?under=True
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Speaker:
    id: str
    name: str
    tagline: str = ""
    bio: str = ""
    photo_url: str = ""


@dataclass
class Talk:
    id: str
    title: str
    description: str = ""
    room: str = ""
    start_time: str = ""
    end_time: str = ""
    speakers: List[Speaker] = None
    event_id: str = ""
    event_name: str = ""

    def __post_init__(self):
        if self.speakers is None:
            self.speakers = []


class Sessionize:
    """Clean Sessionize API scraper"""

    DEFAULT_EVENTS = {
        "amtv2kwb": "PyCon Ireland 2022",
        "jb4vxosa": "PyCon Limerick 2023",
        "jbshwhme": "PyCon Ireland 2023",
    }

    def __init__(self, events: Optional[Dict[str, str]] = None):
        self.events = events or self.DEFAULT_EVENTS
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; PythonIrelandTalkDB/1.0)"}
        )

    def get_all_data(self) -> List[Talk]:
        """Get all talks with speaker information"""
        all_talks = []

        for event_id, event_name in self.events.items():
            logger.info(f"Fetching data for {event_name} ({event_id})")

            try:
                # Get speakers first
                speakers = self._get_speakers(event_id)
                speaker_lookup = {speaker.id: speaker for speaker in speakers}

                # Get sessions and match with speakers
                talks = self._get_talks(event_id, event_name, speaker_lookup)
                all_talks.extend(talks)

            except Exception as e:
                logger.error(f"Failed to fetch data for {event_name}: {e}")
                continue

        return all_talks

    def _get_speakers(self, event_id: str) -> List[Speaker]:
        """Fetch speakers for an event"""
        url = f"https://sessionize.com/api/v2/{event_id}/view/Speakers?under=True"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            speakers_list = soup.find("ul", class_="sz-speakers--list")
            if not speakers_list:
                logger.warning(f"No speakers list found for event {event_id}")
                return []

            speakers = []
            for speaker_el in speakers_list.find_all("li", class_="sz-speaker"):
                speaker = self._parse_speaker(speaker_el)
                if speaker:
                    speakers.append(speaker)

            logger.info(f"Found {len(speakers)} speakers for event {event_id}")
            return speakers

        except requests.RequestException as e:
            logger.error(f"Failed to fetch speakers for {event_id}: {e}")
            return []

    def _parse_speaker(self, speaker_el) -> Optional[Speaker]:
        """Parse a single speaker element"""
        try:
            speaker_id = speaker_el.get("data-speakerid", "").strip()
            if not speaker_id:
                return None

            name_el = speaker_el.find("h3", class_="sz-speaker__name")
            name = name_el.text.strip() if name_el else ""

            tagline_el = speaker_el.find("h4", class_="sz-speaker__tagline")
            tagline = tagline_el.text.strip() if tagline_el else ""

            bio_el = speaker_el.find("p", class_="sz-speaker__bio")
            bio = bio_el.text.strip() if bio_el else ""

            photo_el = speaker_el.find("div", class_="sz-speaker__photo")
            photo_url = ""
            if photo_el:
                img_el = photo_el.find("img")
                if img_el and img_el.get("src"):
                    photo_url = img_el.get("src", "").strip()

            return Speaker(
                id=speaker_id, name=name, tagline=tagline, bio=bio, photo_url=photo_url
            )

        except Exception as e:
            logger.warning(f"Failed to parse speaker: {e}")
            return None

    def _get_talks(
        self, event_id: str, event_name: str, speaker_lookup: Dict[str, Speaker]
    ) -> List[Talk]:
        """Fetch talks for an event"""
        url = f"https://sessionize.com/api/v2/{event_id}/view/Sessions?under=True"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            sessions_list = soup.find("ul", class_="sz-sessions--list")
            if not sessions_list:
                logger.warning(f"No sessions list found for event {event_id}")
                return []

            talks = []
            for session_el in sessions_list.find_all("li", class_="sz-session"):
                talk = self._parse_talk(
                    session_el, event_id, event_name, speaker_lookup
                )
                if talk:
                    talks.append(talk)

            logger.info(f"Found {len(talks)} talks for {event_name}")
            return talks

        except requests.RequestException as e:
            logger.error(f"Failed to fetch talks for {event_id}: {e}")
            return []

    def _parse_talk(
        self,
        session_el,
        event_id: str,
        event_name: str,
        speaker_lookup: Dict[str, Speaker],
    ) -> Optional[Talk]:
        """Parse a single session element"""
        try:
            session_id = session_el.get("data-sessionid", "").strip()
            if not session_id:
                return None

            title_el = session_el.find("h3", class_="sz-session__title")
            title = title_el.text.strip() if title_el else ""

            description_el = session_el.find("p", class_="sz-session__description")
            description = description_el.text.strip() if description_el else ""

            room_el = session_el.find("div", class_="sz-session__room")
            room = room_el.text.strip() if room_el else ""

            # Parse time
            start_time = end_time = ""
            time_el = session_el.find("div", class_="sz-session__time")
            if time_el:
                time_str = time_el.get("data-sztz", "")
                if time_str:
                    time_parts = time_str.split("|")
                    if len(time_parts) >= 3:
                        start_time = time_parts[2].strip()
                    if len(time_parts) >= 4:
                        end_time = time_parts[3].strip()

            # Parse speakers
            speakers = []
            speakers_el = session_el.find("ul", class_="sz-session__speakers")
            if speakers_el:
                for speaker_li in speakers_el.find_all("li"):
                    speaker_id = speaker_li.get("data-speakerid", "").strip()
                    if speaker_id and speaker_id in speaker_lookup:
                        speakers.append(speaker_lookup[speaker_id])

            return Talk(
                id=session_id,
                title=title,
                description=description,
                room=room,
                start_time=start_time,
                end_time=end_time,
                speakers=speakers,
                event_id=event_id,
                event_name=event_name,
            )

        except Exception as e:
            logger.warning(f"Failed to parse talk: {e}")
            return None


# For backward compatibility and testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Sessionize data")
    parser.add_argument("--event-id", type=str, help="Event ID")
    parser.add_argument("--event-name", type=str, help="Event name")
    parser.add_argument(
        "--output", choices=["json", "csv"], default="json", help="Output format"
    )

    args = parser.parse_args()

    events = None
    if args.event_id:
        events = {args.event_id: args.event_name or args.event_id}

    scraper = Sessionize(events=events)
    talks = scraper.get_all_data()

    print(f"Found {len(talks)} talks")
    for talk in talks[:3]:  # Show first 3
        print(f"- {talk.title} by {', '.join(s.name for s in talk.speakers)}")
