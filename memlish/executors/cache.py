from abc import ABC, abstractmethod
import math
from tqdm.auto import tqdm
import pickle
from bson import binary
from typing import Optional
from pymongo import MongoClient
import numpy as np

from jina import DocumentArray, Document, Executor, requests

from memlish.config import MONGODB_CONNECTION_STRING, MONGO_EMBEDDING_DB_NAME
from memlish.executors.bert import RealSBERTEncoder

from memlish.executors.openai_clip import OpenAICLIPTextEncoder, OpenAICLIPImageEncoder


def to_bson_pickle(o): return binary.Binary(pickle.dumps(o))
def from_bson_pickle(o): return pickle.loads(o)


def get_mongo_collection(connection_string, db_name, collection_name):
    client = MongoClient(connection_string)
    assert client.server_info() is not None

    db = client[db_name]
    mongo_collection = db[collection_name]
    return mongo_collection


def read_all_embeddings_map(mongo_collection, emb_col_name):
    emb_map = {}
    for item in mongo_collection.find():
        emb_map[item['_id']] = from_bson_pickle(item[emb_col_name])

    return emb_map


def read_all_embeddings(mongo_collection, emb_col_name):
    filenames, embs = [], []
    for item in mongo_collection.find():
        filenames.append(item['_id'])
        embs.append(from_bson_pickle(item[emb_col_name]))

    return np.array(filenames), np.array(embs)


def yield_batches(li, batch_size):
    n_batches = math.ceil(len(li)/batch_size)
    for i in range(n_batches):
        batch = li[(i)*batch_size:(i+1)*batch_size]
        yield batch


class EmbeddingGeneratorBase(Executor):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def is_valid(self, i): return True

    @abstractmethod
    def get_embeddings(self, docs: Optional[DocumentArray]):
        raise NotImplementedError()


class EmbeddingCache(EmbeddingGeneratorBase):
    embedder = None

    def __init__(self,
                 embedder_params: dict,
                 collection_name: str,
                 megabatch_size: int,
                 embedding_field_name: str,
                 connection_string=MONGODB_CONNECTION_STRING,
                 db_name=MONGO_EMBEDDING_DB_NAME,
                 **kwargs,
                 ):
        super().__init__(**kwargs)

        self.mongo_collection = self.get_mongo_collection(
            connection_string, db_name, collection_name)
        self.embedder = self.embedder(
            **embedder_params) if self.embedder else None
        self.embedding_field_name = embedding_field_name
        self.megabatch_size = megabatch_size
        self.collection_name = collection_name

    @staticmethod
    def get_mongo_collection(connection_string, db_name, collection_name):
        client = MongoClient(connection_string)
        assert client.server_info() is not None

        db = client[db_name]
        mongo_collection = db[collection_name]
        return mongo_collection

    @staticmethod
    def read_all_embeddings(collection_name,
                            connection_string=MONGODB_CONNECTION_STRING,
                            db_name=MONGO_EMBEDDING_DB_NAME,
                            embedding_field_name='emb'):
        mongo_collection = EmbeddingCache.get_mongo_collection(
            connection_string, db_name, collection_name)

        return read_all_embeddings_map(mongo_collection, embedding_field_name)

    @classmethod
    def create_default(cls,
                       embedder_params: dict,
                       collection_name,
                       connection_string=MONGODB_CONNECTION_STRING,
                       db_name=MONGO_EMBEDDING_DB_NAME,
                       embedding_field_name='emb',
                       megabatch_size=4096):

        mongo_collection = EmbeddingCache.get_mongo_collection(
            connection_string, db_name, collection_name)

        return cls(embedder_params=embedder_params,
                   mongo_collection=mongo_collection,
                   collection_name=collection_name,
                   embedding_field_name=embedding_field_name,
                   megabatch_size=megabatch_size,
                   )

    @requests
    def get_embeddings(self, docs: Optional[DocumentArray], **kwargs):
        emb_map = self.get_existing_embeddings()

        idxs_to_process = []
        for i, d in enumerate(docs):
            emb = emb_map.get(d.id)
            if emb is None:
                idxs_to_process.append(i)
            else:
                d.embedding = emb

        if self.embedder is None:
            return

        n_batches = math.ceil(len(idxs_to_process)/self.megabatch_size)

        for idx_batch in tqdm(yield_batches(idxs_to_process, batch_size=self.megabatch_size), total=n_batches):
            docs_batch = docs[idx_batch]
            self.embedder.get_embeddings(docs_batch, **kwargs)
            self._write_embeddings(docs_batch)

    def get_existing_embeddings(self):
        return read_all_embeddings_map(self.mongo_collection, self.embedding_field_name)

    def _write_embeddings(self, docs):
        db_entries = [{
            "_id": i.id,
            self.embedding_field_name: to_bson_pickle(i.embedding)
        } for i in docs]

        self.mongo_collection.insert_many(db_entries)


class OpenAICLIPImageEncoderCache(EmbeddingCache):
    embedder = OpenAICLIPImageEncoder


class OpenAICLIPTextEncoderCache(EmbeddingCache):
    embedder = OpenAICLIPTextEncoder


class RealSBERTEncoderCache(EmbeddingCache):
    embedder = RealSBERTEncoder
