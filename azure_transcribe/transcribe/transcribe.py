import time
import json
from contextlib import suppress

import requests
from urllib.parse import urljoin
from uuid import uuid4
from datetime import timedelta

from django.utils import timezone

from azure_transcribe.fixtures.azure_transcribe_states import AzureTranscribeStates


class AzureTranscribe:
    """
    Class for creating a transcription job in Azure Transcribe and getting the result.
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.token
        }

    def create_transcription(self, sas_url: str, language: str = 'en-US') -> str:
        url = urljoin(self.base_url, 'transcriptions')
        payload = {
            "contentUrls": [
                sas_url
            ],
            "locale": language,
            "displayName": str(uuid4())
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['self']

    def check_status(self, transcription_url: str, time_sleep: float = 15, time_out: float = 600) -> dict:
        start = timezone.now()
        while True:
            response = requests.get(transcription_url, headers=self.headers)
            status = response.json()['status']
            files_url = response.json()['links']['files']
            error = response.json()['properties'].get('error')

            if status in [AzureTranscribeStates.SUCCEEDED, AzureTranscribeStates.FAILED]:
                return {
                    'status': status,
                    'files_url': files_url,
                    'error': error
                }
            time.sleep(time_sleep)
            if timezone.now() > start + timedelta(seconds=time_out):
                raise TimeoutError

    def get_result(self, files_url: str) -> str:
        response = requests.get(files_url, headers=self.headers)
        file_url = response.json()['values'][1]['links']['contentUrl']
        response = requests.get(file_url)
        phrases = response.json()['combinedRecognizedPhrases']
        if bool(phrases):
            return phrases[0]['display']
        return str()
