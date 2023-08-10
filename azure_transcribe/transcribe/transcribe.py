import datetime
import time
import json
from typing import List, Dict, Union

import requests
from urllib.parse import urljoin
from uuid import uuid4
from datetime import timedelta, datetime

from azure_transcribe.fixtures.azure_transcribe_states import AzureTranscribeStates, AzureTranscribeStatus, \
    TRANSCRIPTION_KIND, AzureTranscribeResult, AzureDialogTranscript


class AzureTranscribeMono:
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

    def check_status(self, transcription_url: str, time_sleep: float = 15,
                     time_out: float = 600) -> AzureTranscribeStatus:
        start = datetime.now()
        while True:
            response = requests.get(transcription_url, headers=self.headers)
            status = response.json()['status']

            if status in [AzureTranscribeStates.SUCCEEDED, AzureTranscribeStates.FAILED]:
                return {
                    'status': status,
                    'files_url': response.json()['links']['files'],
                    'error': response.json()['properties'].get('error')
                }
            time.sleep(time_sleep)
            if datetime.now() > start + timedelta(seconds=time_out):
                raise TimeoutError

    @classmethod
    def get_transcription_url(cls, obj: Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]) -> str:
        values = obj.get('values', [])
        for value in values:
            if value.get('kind') == 'Transcription':
                return value['links']['contentUrl']

    @classmethod
    def prepare_dialog(cls, data: List[Dict[str, List[Dict[str, Union[str, List]]]]]) -> List[AzureDialogTranscript]:
        dialog = [{'speaker': data[0].get('speaker'), 'text': ''}]
        for phase in data:
            if phase['speaker'] == dialog[-1]['speaker']:
                dialog[-1]['text'] += ' ' + phase['nBest'][0]['display']
            else:
                dialog.append({'speaker': phase['speaker'], 'text': phase['nBest'][0]['display']})
        return dialog

    @classmethod
    def parse_reponse(cls, response) -> AzureTranscribeResult:
        text, dialog_text = '', ''
        full_transcript = response['combinedRecognizedPhrases']
        dialog_transcript = response['recognizedPhrases']
        if full_transcript:
            text = full_transcript[0]['display']
        if dialog_transcript:
            dialog_text = cls.prepare_dialog(dialog_transcript)

        return {'full_transcript': text,
                'dialog_transcript': dialog_text,
                'source': response.get('source')}

    def get_result(self, files_url: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        recognized_data = {}
        response = requests.get(files_url, headers=self.headers)
        file_url = self.get_transcription_url(response.json())
        if file_url:
            response = requests.get(file_url)
            response_json = response.json()
            recognized_data = self.parse_reponse(response_json)
        return recognized_data


class AzureTranscribeBatchMono(AzureTranscribeMono):
    """
    Class for creating a mono-batch-transcription job in Azure Transcribe and getting the result.
    """

    def create_transcription(self, sas_urls: List[str], language: str = 'en-US') -> str:
        url = urljoin(self.base_url, 'transcriptions')
        payload = {
            "contentUrls": sas_urls,
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
        return response.json().get('self')

    @classmethod
    def get_transcription_urls(cls, obj: Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]) -> List[str]:
        transcription_urls, values = [], obj.get('values', [])
        for value in values:
            if value.get('kind') == TRANSCRIPTION_KIND:
                transcription_urls.append(value['links']['contentUrl'])
        return transcription_urls

    def get_result(self, files_url: str) -> List[AzureTranscribeResult]:
        text, dialog_text, jsons = str(), list(), list()
        response = requests.get(files_url, headers=self.headers)
        file_urls = self.get_transcription_urls(response.json())

        for file_url in file_urls:
            response = requests.get(file_url)
            response_json = response.json()
            recognized_data = self.parse_reponse(response_json)
            jsons.append(recognized_data or {})

        return jsons


class AzureTranscribeBatchStereo(AzureTranscribeBatchMono):
    """
        Class for creating a stereo-batch-transcription job in Azure Transcribe and getting the result.
    """

    @classmethod
    def prepare_dialog(cls, data) -> List[Dict[str, str]]:
        data.sort(key=lambda x: x.get('offset'))
        dialog = [{'speaker': data[0].get('channel'), 'text': ''}]
        for phrase in data:
            if phrase['channel'] == dialog[-1]['speaker']:
                dialog[-1]['text'] += (' ' + phrase['nBest'][0]['display']).strip()
            else:
                dialog.append({'speaker': phrase['channel'], 'text': phrase['nBest'][0]['display'].strip()})
        return dialog

    @classmethod
    def parse_reponse(cls, response):
        dialog_text, dialog_transcript = response['recognizedPhrases'], list()
        if dialog_transcript:
            dialog_text = cls.prepare_dialog(dialog_transcript)

        full_transcript = response['combinedRecognizedPhrases']
        text = ''
        for index, transcript in enumerate(full_transcript):
            text += f'Speaker {index + 1}:\n{transcript["display"]}\n\n'

        return {'full_transcript': text,
                'dialog_transcript': dialog_text,
                'source': response['source']}
