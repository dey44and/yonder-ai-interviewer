from datetime import datetime
import json


class TranscriptService:
    def __init__(self):
        self.transcript = []

    def add_message(self, sender: str, message, timestamp: datetime):
        entry = {"sender": sender, "message": message, "timestamp": timestamp}
        self.transcript.append(entry)

    def export_conversation(self, path: str):
        with open(path, "w") as f:
            json.dump(self.transcript, f, indent=4)
