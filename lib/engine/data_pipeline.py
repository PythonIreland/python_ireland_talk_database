# lib/engine/data_pipeline.py
from .sessionize import Sessionize, Talk
from .elasticsearch_client import ElasticsearchClient
from typing import Dict, List
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self):
        self.es_client = ElasticsearchClient()

    def ingest_sessionize_data(self, events: Dict[str, str]) -> int:
        """Ingest data from Sessionize and store in Elasticsearch"""
        sessionize = Sessionize(events=events)
        talks = sessionize.get_all_data()
        return self.ingest_talks(talks)

    def ingest_talks(self, talks: List[Talk]) -> int:
        """Ingest Talk objects directly into Elasticsearch"""
        # Make sure index exists
        self.es_client.create_talk_index()

        processed_count = 0
        for talk in talks:
            try:
                processed_talk = self._process_talk_object(talk)
                talk_id = self.es_client.index_talk(processed_talk)
                logger.info(f"Indexed talk: {talk.title} (ID: {talk_id})")
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process talk {talk.id}: {e}")
                continue

        logger.info(f"Successfully processed {processed_count} talks")
        return processed_count

    def _process_talk_object(self, talk: Talk) -> Dict:
        """Process Talk dataclass object for Elasticsearch"""
        return {
            "id": talk.id,
            "event_id": talk.event_id,
            "event_name": talk.event_name,
            "title": talk.title,
            "description": talk.description,
            "room": talk.room,
            "start_time": talk.start_time,
            "end_time": talk.end_time,
            "speaker_names": [s.name for s in talk.speakers],
            "speaker_bios": [s.bio for s in talk.speakers if s.bio],
            "speaker_taglines": [s.tagline for s in talk.speakers if s.tagline],
            "speaker_photos": [s.photo_url for s in talk.speakers if s.photo_url],
            "tags": [],
            "auto_tags": self._extract_auto_tags_from_talk(talk),
            "manual_tags": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _extract_auto_tags_from_talk(self, talk: Talk) -> List[str]:
        """Extract basic tags from Talk object"""
        text = f"{talk.title} {talk.description}".lower()
        keywords = []

        # AI/ML detection
        ai_keywords = [
            "ai",
            "machine learning",
            "neural",
            "deep learning",
            "llm",
            "gpt",
            "artificial intelligence",
            "tensorflow",
            "pytorch",
            "scikit",
            "model",
        ]
        if any(keyword in text for keyword in ai_keywords):
            keywords.append("AI/ML")

        # Web Development
        web_keywords = [
            "django",
            "flask",
            "fastapi",
            "web",
            "http",
            "api",
            "rest",
            "graphql",
            "html",
            "css",
            "javascript",
            "react",
            "vue",
            "frontend",
            "backend",
        ]
        if any(keyword in text for keyword in web_keywords):
            keywords.append("Web Development")

        # Data Science
        data_keywords = [
            "pandas",
            "numpy",
            "data",
            "analysis",
            "visualization",
            "jupyter",
            "matplotlib",
            "seaborn",
            "plotly",
            "analytics",
            "statistics",
        ]
        if any(keyword in text for keyword in data_keywords):
            keywords.append("Data Science")

        # Testing
        test_keywords = [
            "test",
            "pytest",
            "unittest",
            "tdd",
            "testing",
            "mock",
            "fixture",
        ]
        if any(keyword in text for keyword in test_keywords):
            keywords.append("Testing")

        # DevOps
        devops_keywords = [
            "docker",
            "kubernetes",
            "k8s",
            "ci/cd",
            "deployment",
            "aws",
            "cloud",
        ]
        if any(keyword in text for keyword in devops_keywords):
            keywords.append("DevOps")

        # Python Core
        python_keywords = [
            "asyncio",
            "async",
            "await",
            "decorators",
            "generators",
            "metaclass",
        ]
        if any(keyword in text for keyword in python_keywords):
            keywords.append("Python Core")

        return keywords
