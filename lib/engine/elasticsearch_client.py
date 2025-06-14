# lib/engine/elasticsearch_client.py
from elasticsearch import Elasticsearch
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


# lib/engine/elasticsearch_client.py
from elasticsearch import Elasticsearch


class ElasticsearchClient:
    def __init__(self, host: str = "localhost", port: int = 9200):
        self.host = host
        self.port = port
        # Add compatibility headers for ES 8.x
        self.es = Elasticsearch(
            [f"http://{host}:{port}"],
            verify_certs=False,
            headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
        )

    def is_healthy(self) -> bool:
        """Check if Elasticsearch is healthy"""
        try:
            health = self.es.cluster.health()
            return health["status"] in ["yellow", "green"]
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False

    def create_talk_index(self) -> bool:
        """Create index for talk documents"""
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "event_id": {"type": "keyword"},
                    "event_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "description": {"type": "text", "analyzer": "standard"},
                    "room": {"type": "keyword"},
                    "start_time": {"type": "keyword"},
                    "end_time": {"type": "keyword"},
                    "speaker_names": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "speaker_bios": {"type": "text"},
                    "speaker_taglines": {"type": "text"},
                    "speaker_photos": {"type": "keyword"},
                    "auto_tags": {"type": "keyword"},
                    "manual_tags": {"type": "keyword"},
                    "tags": {
                        "type": "nested",
                        "properties": {
                            "category": {"type": "keyword"},
                            "subcategory": {"type": "keyword"},
                            "confidence": {"type": "float"},
                            "user_added": {"type": "boolean"},
                        },
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            }
        }

        try:
            if not self.es.indices.exists(index="talks"):
                self.es.indices.create(index="talks", body=mapping)
                logger.info("Created 'talks' index")
                return True
            else:
                logger.info("'talks' index already exists")
                return True
        except Exception as e:
            logger.error(f"Failed to create talks index: {e}")
            return False

    def index_talk(self, talk_data: Dict[str, Any]) -> str:
        """Index a single talk"""
        try:
            response = self.es.index(
                index="talks",
                id=talk_data.get("id"),  # Use talk ID as document ID
                body=talk_data,
            )
            return response["_id"]
        except Exception as e:
            logger.error(f"Failed to index talk: {e}")
            raise

    def get_talk(self, talk_id: str) -> Optional[Dict]:
        """Get a single talk by ID"""
        try:
            response = self.es.get(index="talks", id=talk_id)
            return response["_source"]
        except Exception as e:
            logger.error(f"Failed to get talk {talk_id}: {e}")
            return None

    def search_talks(self, query: Dict[str, Any]) -> List[Dict]:
        """Search talks with filters"""
        try:
            response = self.es.search(index="talks", body=query)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def update_talk_tags(self, talk_id: str, tags: List[str]) -> bool:
        """Update manual tags for a talk"""
        try:
            self.es.update(
                index="talks",
                id=talk_id,
                body={"doc": {"manual_tags": tags, "updated_at": "now"}},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update tags for talk {talk_id}: {e}")
            return False

    def get_all_events(self) -> List[str]:
        """Get list of all event names"""
        try:
            query = {
                "size": 0,
                "aggs": {
                    "events": {"terms": {"field": "event_name.keyword", "size": 100}}
                },
            }
            response = self.es.search(index="talks", body=query)
            buckets = response["aggregations"]["events"]["buckets"]
            return [bucket["key"] for bucket in buckets]
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []

    def get_all_tags(self) -> Dict[str, int]:
        """Get all tags with their counts"""
        try:
            query = {
                "size": 0,
                "aggs": {
                    "auto_tags": {"terms": {"field": "auto_tags", "size": 100}},
                    "manual_tags": {"terms": {"field": "manual_tags", "size": 100}},
                },
            }
            response = self.es.search(index="talks", body=query)

            tags = {}
            for bucket in response["aggregations"]["auto_tags"]["buckets"]:
                tags[bucket["key"]] = bucket["doc_count"]
            for bucket in response["aggregations"]["manual_tags"]["buckets"]:
                key = bucket["key"]
                tags[key] = tags.get(key, 0) + bucket["doc_count"]

            return tags
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return {}

    def delete_all_talks(self) -> bool:
        """Delete all talks (useful for testing)"""
        try:
            self.es.delete_by_query(index="talks", body={"query": {"match_all": {}}})
            logger.info("Deleted all talks")
            return True
        except Exception as e:
            logger.error(f"Failed to delete talks: {e}")
            return False

    def get_talk_count(self) -> int:
        """Get total number of talks"""
        try:
            response = self.es.count(index="talks")
            return response["count"]
        except Exception as e:
            logger.error(f"Failed to get talk count: {e}")
            return 0
