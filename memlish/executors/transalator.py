from jina import DocumentArray, Executor, requests, Document
from typing import Optional, Tuple, Sequence, Dict
from memlish.io.timelog import log_duration
from memlish.lang_detector import FasttextLanguageDetector
from memlish.config import AWS_REGION
import boto3


class AwsTranslator(Executor):

    def __init__(
        self,
        region_name=AWS_REGION,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.lang_detector = FasttextLanguageDetector()
        self.translator = boto3.client(
            service_name='translate', region_name=region_name, use_ssl=True)

    @requests
    @log_duration
    def process_doc(self, docs: Optional[DocumentArray], parameters: Dict = {}, **kwargs):
        if docs is None:
            return

        for doc in docs:
            lang = self.lang_detector.detect_lang(doc.text)
            if lang != 'en':
                translator_res = self.translator.translate_text(
                    Text=doc.text, SourceLanguageCode='auto', TargetLanguageCode="en")
                print(translator_res)
                doc.text = translator_res.get('TranslatedText')
