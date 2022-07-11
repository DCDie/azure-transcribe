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
            "displayName": str(uuid4()),
            "properties": {
                "diarizationEnabled": True,
                "wordLevelTimestampsEnabled": True,
                "punctuationMode": "DictatedAndAutomatic"
            }
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

    @classmethod
    def prepare_dialog(cls, data: List[Dict[str, List[Dict[str, Union[str, List]]]]]) -> List[Dict[str, str]]:
        dialog = [{'speaker': data[0].get('speaker'), 'text': ''}]
        for phase in data:
            if phase['speaker'] == dialog[-1]['speaker']:
                dialog[-1]['text'] += ' ' + phase['nBest'][0]['display']
            else:
                dialog.append({'speaker': phase['speaker'], 'text': phase['nBest'][0]['display']})
        return dialog

    def get_result(self, files_url: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        text = str()
        dialog_text = list()
        response = requests.get(files_url, headers=self.headers)
        file_url = self.get_transcription_url(response.json())
        if file_url:
            response = requests.get(file_url)
            response_json = response.json()
            full_transcript = response_json['combinedRecognizedPhrases']
            dialog_transcript = response_json['recognizedPhrases']
            if bool(full_transcript):
                text = full_transcript[0]['display']
            if bool(dialog_transcript):
                dialog_text = self.prepare_dialog(dialog_transcript)
        return {
            'full_transcript': text,
            'dialog_transcript': dialog_text
        }
