from urllib.parse import urljoin
from uuid import uuid4

from datetime import datetime, timedelta
from azure.storage.blob import BlobClient, generate_blob_sas, BlobSasPermissions, BlobServiceClient


class BlobService:
    def __init__(self, account_namae, account_key, container, blob, conn_str):
        self.account_name = 'my2022storage'
        self.account_key = 'Ni/DPFIpxm5D/5rpjuxhBlTT53MI7bVryKs6WkDXVuBEEM3bfRRpQcd1XlvTdOJVRRY8/HRW+nT4+ASt6VUSUQ=='
        self.container_name = 'newcontainer'
        self.blob_name = 'another_one.mp3'
        self.connect_str = 'DefaultEndpointsProtocol=https;AccountName=my2022storage;AccountKey=Ni/DPFIpxm5D' \
                           '/5rpjuxhBlTT53MI7bVryKs6WkDXVuBEEM3bfRRpQcd1XlvTdOJVRRY8/HRW+nT4+ASt6VUSUQ==;EndpointSuffix=core' \
                           '.windows.net '
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)

    def post_blob(self, file_name):
        file = file_name
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file)
        with open(file, "rb") as data:
            blob_client.upload_blob(data)


class AzureTranscribe:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.token
        }

    def create_transcription(self, file_url: str, language: str = 'en-US') -> dict:
        url = urljoin(self.base_url, 'transcriptions')
        payload = {
            "contentUrls": [
                file_url
            ],
            "locale": language,
            "displayName": f"{uuid4()}"
        }
        return dict()


def get_blob_sas(account_name, account_key, container_name, blob_name):
    sas_blob = generate_blob_sas(account_name=account_name,
                                 container_name=container_name,
                                 blob_name=blob_name,
                                 account_key=account_key,
                                 permission=BlobSasPermissions(read=True),
                                 expiry=datetime.utcnow() + timedelta(hours=1))
    return sas_blob


blob = get_blob_sas(account_name, account_key, container_name, blob_name)
url = 'https://' + account_name + '.blob.core.windows.net/' + container_name + '/' + blob_name + '?' + blob
