#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/7/7 2:53 PM
# @Author  : suchang
# @File    : __init__.py.py

import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    PATIENTS_PRE_PAGE = 20
    MONGO_URI = "mongodb://superversion:bjfupj2018@localhost:27017/supervision"
    MONGO_HOST = "localhost"
    MONGO_USERNAME = 'superversion'
    MONGO_DBNAME = 'supervision'
    MONGO_PASSWORD = 'bjfupj2018'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    THREADED = True
    MONGO_PORT = 27017
    MAIL_DEBUG = True
    SQLALCHEMY_DATABASE_URI = \
        "mysql+pymysql://root:wshwoaini@localhost:3306/supervision?charset=utf8mb4"
    KAFLKA_HOST = ["47.92.110.74:9092", ]
    KAFLKA_TOPIC = "bjfu_calculate_send_topic"

    REDIS_URL = "redis://@localhost:6379/1"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
