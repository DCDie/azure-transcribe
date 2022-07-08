import datetime
import time
import json
from typing import List, Dict, Union

import requests
from urllib.parse import urljoin
from uuid import uuid4
from datetime import timedelta, datetime

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

    def check_status(self, transcription_url: str, time_sleep: float = 15, time_out: float = 600) -> Dict[str, str]:
        start = datetime.now()
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
            if datetime.now() > start + timedelta(seconds=time_out):
                raise TimeoutError

    @classmethod
    def get_transcription_url(cls, obj: Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]) -> str:
        values = obj.get('values')
        if values:
            for value in values:
                if value.get('kind') == 'Transcription':
                    return value['links']['contentUrl']

    def get_result(self, files_url: str) -> str:
        response = requests.get(files_url, headers=self.headers)
        file_url = self.get_transcription_url(response.json())
        if file_url:
            response = requests.get(file_url)
            phrases = response.json()['combinedRecognizedPhrases']
            if bool(phrases):
                return phrases[0]['display']
        return str()
