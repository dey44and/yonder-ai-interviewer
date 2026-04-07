from datetime import datetime
import json
from typing import List, Dict


class TranscriptService:
    def __init__(self):
        self._transcript = []

    @property
    def transcript(self) -> List[Dict[str, any]]:
        return self._transcript

    def add_message(self, sender: str, message, timestamp: datetime):
        entry = {"sender": sender, "message": message, "timestamp": timestamp}
        self._transcript.append(entry)

    def export_conversation(self, path: str):
        with open(path, "w") as f:
            json.dump(self._transcript, f, indent=4)
