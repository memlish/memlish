import urllib.request
from pathlib import Path
import spacy
import fasttext


FMODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"


class FasttextLanguageDetector():
    def __init__(self, model_path=None, load_model_to_dir='/tmp/'):
        if model_path is None:
            model_path = self._download_model(load_model_to_dir)
        self.fmodel = fasttext.load_model(model_path)
        self.nlp = spacy.load('en_core_web_sm')

    def detect_lang(self, text):
        lang, _ = self.fmodel.predict([text.replace('\n', ' ')])
        return lang[0][0].replace('__label__', '')

    def count_lang_chars(self, text):
        doc = self.nlp(text)

        dist = {}
        for sent in doc.sents:
            lang = self.detect_lang(str(sent))
            sent_len = len(str(sent))
            if lang in dist:
                dist[lang] += sent_len
            else:
                dist[lang] = sent_len
        return dist

    def _download_model(self, load_model_to_dir):
        destination_path = Path(load_model_to_dir) / \
            'fasttext_lang_detect_model.bin'
        if not destination_path.exists():
            urllib.request.urlretrieve(FMODEL_URL, destination_path)
        return str(destination_path)
