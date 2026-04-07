from transformers import pipeline
from typing import Dict, Union, List


class TextAnalysisService:
    def __init__(self):
        self.sentiment_pipeline = pipeline("sentiment-analysis")

    def analyze_transcript(
        self, transcript: List[Dict[str, any]]
    ) -> List[Dict[str, Union[str, float]]]:
        responses = " ".join(
            [
                response["message"]
                for response in transcript
                if isinstance(response["message"], str)
            ]
        )
        return self.sentiment_pipeline(responses)
