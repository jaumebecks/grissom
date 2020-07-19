# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import logging

from notifiers import Notifier
from async.notifiers import pushbullet
from lib import mongo

logger = logging.getLogger(__name__)


class Pipeline:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        raise NotImplementedError()

    @staticmethod
    def complete_item(item, data):
        item.update(data)


class MongoPipeline(Pipeline):
    def __init__(self, host, port, database):
        self.host = host
        self.port = port
        self.database = database

    @classmethod
    def from_crawler(cls, crawler):
        mongo_host = crawler.settings.get('MONGO_HOST')
        mongo_port = crawler.settings.get('MONGO_PORT')
        mongo_database = crawler.settings.get('MONGO_DATABASE')
        return cls(mongo_host, mongo_port, mongo_database)

    def open_spider(self, spider):
        self.client = mongo.Client(self.host, self.port, self.database)
        self.collection = self.client[spider.name]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        raise NotImplementedError()


class SaveOnMongo(MongoPipeline):
    IGNORE_KEYS = []

    def process_item(self, item, spider):

        item_dict = item.to_dict()

        pk_name = item_dict.get('pk')
        pk_value = item_dict.get(pk_name)
        saved = self.collection.find_one({pk_name: pk_value})

        if not saved:
            self.insert_item(item_dict)

        return item

    def insert_item(self, item):
        logger.info('Saving item in database')
        self.remove_useless_keys(item)
        self.complete_item(item, {
            'notified': Notifier.STATUS_PENDING,
            'notified_at': None,
        })

        self.collection.insert(item)

    @classmethod
    def remove_useless_keys(cls, item):
        for key in cls.IGNORE_KEYS:
            item.pop(key)


class ScheduleNotifications(Pipeline):

    def __init__(self, pushbullet_enabled):
        self.pushbullet_enabled = pushbullet_enabled

    @classmethod
    def from_crawler(cls, crawler):
        pushbullet_enabled = crawler.settings.get('PUSHBULLET_ENABLED')
        return cls(pushbullet_enabled)

    def process_item(self, item, spider):
        if self.pushbullet_enabled:
            item_dict = item.to_dict()
            self.pushbullet(item_dict)
        return item

    @classmethod
    def pushbullet(cls, item):
        pushbullet.delay(item)
