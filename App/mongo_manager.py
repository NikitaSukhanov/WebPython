import pymongo
from pymongo.bulk import BulkOperationBuilder


class MongoCollectionManager:
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 27017

    def __init__(self, db_name, collection_name, max_buffer_size=100,
                 host=DEFAULT_HOST, port=DEFAULT_PORT, **kwargs):
        self._client = pymongo.MongoClient(host=host, port=port, **kwargs)
        self._db = self._client[db_name]
        self._collection = self._db[collection_name]
        self._buffer = BulkOperationBuilder(self._collection, ordered=False)
        self._buffer_size = 0
        self._max_buffer_size = max_buffer_size

    def __len__(self):
        return self.count_filtered(docs_filter={})

    def __iter__(self):
        return self.collection.find()

    def __getitem__(self, item_id):
        return self.collection.find_one({"_id": item_id})

    @property
    def db(self):
        self.buffer_flush()
        return self._db

    @property
    def collection(self):
        self.buffer_flush()
        return self._collection

    def insert(self, item, item_id=None, replace=False, **kwargs):
        self.buffer_flush()
        if item_id is None:
            return self.collection.insert_one(item, **kwargs)
        item['_id'] = item_id
        kwargs['filter'] = {"_id": item_id}
        kwargs['upsert'] = True
        if replace:
            kwargs['update'] = {"$set": item}
        else:
            kwargs['update'] = {"$setOnInsert": item}
        return self.collection.update_one(**kwargs)

    def insert_buffered(self, item, item_id=None, replace=False):
        if item_id is None:
            self._buffer.insert(item)
        item['_id'] = item_id
        if replace:
            update = {"$set": item}
        else:
            update = {"$setOnInsert": item}
        self._buffer.find({"_id": item_id}).upsert().update_one(update=update)
        self._buffer_size += 1
        if self._buffer_size >= self._max_buffer_size:
            self.buffer_flush()

    def buffer_flush(self):
        if self._buffer_size == 0:
            return
        response = self._buffer.execute()
        self.buffer_clear()
        return response

    def buffer_clear(self):
        self._buffer = BulkOperationBuilder(self._collection, ordered=False)
        self._buffer_size = 0

    def count_filtered(self, docs_filter, **kwargs):
        return self.collection.count_documents(filter=docs_filter, **kwargs)

    def find_by_id_list(self, id_list):
        return self.collection.find({'_id': {'$in': id_list}})
