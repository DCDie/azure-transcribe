import time
from urllib.parse import urljoin
from uuid import uuid4

from datetime import datetime, timedelta

import requests
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient


class BlobService:
    def __init__(self, account_name, account_key, container, conn_str):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container
        self.connect_str = conn_str
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)

    def post_blob(self, file_name):
        file = file_name
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file)
        with open(file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    def get_blob_sas(self, file_name):
        sas_blob = generate_blob_sas(account_name=self.account_name,
                                     container_name=self.container_name,
                                     blob_name=file_name,
                                     account_key=self.account_key,
                                     permission=BlobSasPermissions(read=True),
                                     expiry=datetime.utcnow() + timedelta(hours=3))
        url = 'https://' + self.account_name + '.blob.core.windows.net/' + self.container_name + '/' + file_name + '?' + sas_blob
        return url


class AzureTranscribe:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.token
        }

    def create_transcription(self, sas_url: str, language: str = 'en-US') -> dict:
        url = urljoin(self.base_url, 'transcriptions')
        payload = {
            "contentUrls": [
                sas_url
            ],
            "locale": language,
            "displayName": f"{uuid4()}"
        }
        import json
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['self']

    def check_status(self, transcription_url):
        for i in range(40):
            response = requests.get(transcription_url, headers=self.headers)
            if response.json()['status'] == 'Succeeded':
                return response.json()['links']['files']
            time.sleep(15)
            if i == 39:
                raise TimeoutError

    def get_result(self, files_url):
        response = requests.get(files_url, headers=self.headers)
        file_url = response.json()['values'][1]['links']['contentUrl']
        response = requests.get(file_url)
        return response.json()['combinedRecognizedPhrases'][0]['display']
