import app.core.dao as dao
from app.utils import CustomError, db
from app import redis_cli
from app.streaming import send_kafka_message
from app.utils.Error import CustomError
import pandas
import datetime
import json


class LessonRecordController(object):
    @classmethod
    def formatter(cls, lesson_record):
        return lesson_record

    @classmethod
    def reformatter_insert(cls, data: dict):
        return data

    @classmethod
    def reformatter_update(cls, data: dict):
        return data

    @classmethod
    def reformatter_query(cls, data: dict):
        return data

    @classmethod
    def query_lesson_records_history(cls, query_dict: dict, unscoped: bool = False):
        (lesson_records, num) = dao.LessonRecord.query_lesson_records(query_dict=query_dict, unscoped=unscoped)
        return [cls.formatter(lesson_record) for lesson_record in lesson_records], num

    @classmethod
    def query_lesson_records_term(cls, term: str = None, query_dict: dict = {}, unscoped: bool = False):
        if term is None:
            term = dao.Term.get_now_term()['name']
        query_dict['term'] = [term]
        (lesson_records, num) = dao.LessonRecord.query_lesson_records(query_dict=query_dict, unscoped=unscoped)
        return [cls.formatter(lesson_record) for lesson_record in lesson_records], num

    @classmethod
    def query_lesson_record_history(cls, username: str = None, query_dict: dict = {}, unscoped: bool = False):
        query_dict['username'] = [username]
        (lesson_records, num) = dao.LessonRecord.query_lesson_records(query_dict=query_dict, unscoped=unscoped)
        return [cls.formatter(lesson_record) for lesson_record in lesson_records], num

    @classmethod
    def get_lesson_record(cls, username: str = None, term: str = None, unscoped: bool = False):
        if term is None:
            term = dao.Term.get_now_term()['name']
        lesson_record = dao.LessonRecord.get_lesson_record(username=username, term=term, unscoped=unscoped)
        return cls.formatter(lesson_record)

    @classmethod
    def delete_lesson_record(cls, ctx: bool = True, username: str = None, term: str = None):
        if term is None:
            term = dao.Term.get_now_term()['name']
        lesson_record = dao.LessonRecord.get_lesson_record(username=username, term=term, unscoped=False)
        try:
            dao.LessonRecord.delete_lesson_record(ctx=False, query_dict={'id': [lesson_record['id']]})
            if ctx:
                db.session.commit()
        except Exception as e:
            if ctx:
                db.session.rollback()
            if isinstance(e, CustomError):
                raise e
            else:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_lesson_records(cls, ctx: bool = True, usernames: list = []):
        term = dao.Term.get_now_term()['name']
        try:
            for username in usernames:
                supervisor_query_dict = {'term': [term], 'username': [username]}
                user = dao.User.get_user(username=username, unscoped=False)
                (supervisors, num) = dao.Supervisor.query_supervisors(query_dict=supervisor_query_dict, unscoped=False)
                for supervisor in supervisors:
                    (_, num) = dao.LessonRecord.query_lesson_records(
                        query_dict={'username': [username], 'term': [term]}, unscoped=False)
                    if num == 0:
                        data = {'term': term, 'username': username, 'group_name': supervisor['group'],
                                'name': user['name']}
                        dao.LessonRecord.insert_lesson_record(ctx=False, data=data)
            if ctx:
                db.session.commit()
        except Exception as e:
            if ctx:
                db.session.rollback()
            if isinstance(e, CustomError):
                raise e
            else:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def insert_lesson_record(cls, ctx: bool = True, username: str = None, term: str = None):
        user = dao.User.get_user(username=username, unscoped=False)
        supervisor = dao.Supervisor.get_supervisor(username=username, term=term, unscoped=False)
        try:
            data = {'username': username, 'term': term, 'name': user['name'], 'group_name': supervisor['group']}
            dao.LessonRecord.insert_lesson_record(ctx=False, data=data)
            if ctx:
                db.session.commit()
        except Exception as e:
            if ctx:
                db.session.rollback()
            if isinstance(e, CustomError):
                raise e
            else:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_lesson_record(cls,ctx:bool=True, username:str=None, term:str=None, data:dict={}):
        lesson_record = dao.LessonRecord.get_lesson_record(username=username, term=term, unscoped=False)
        try:
            dao.LessonRecord.update_lesson_record(query_dict={'id':[lesson_record['id']]}, data=data)
            if ctx:
                db.session.commit()
        except Exception as e:
            if ctx:
                db.session.rollback()
            if isinstance(e, CustomError):
                raise e
            else:
                raise CustomError(500, 500, str(e))
        return True
