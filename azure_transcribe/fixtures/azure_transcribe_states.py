from typing import TypedDict, List


class AzureTranscribeStates(object):
    """
    Class for storing the states of Azure Transcribe.
    """
    NOT_STARTED = "NotStarted"
    RUNNING = "Running"
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"


TRANSCRIPTION_KIND = 'Transcription'


class AzureTranscribeStatus(TypedDict):
    error: str
    files_url: str
    status: AzureTranscribeStates


class AzureDialogTranscript(TypedDict):
    text: str
    speaker: str


class AzureTranscribeResult(TypedDict):
    source: str
    full_transcript: str
    dialog_transcript: List[AzureDialogTranscript]
