from app.utils.mysql import db
import app.utils.url_condition.url_condition_mysql as mysql_url_condition
import app.utils.url_condition.url_condition_mongodb as mongodb_url_condition
from app.utils.Error import CustomError
from flask_login import current_user
from datetime import datetime


class FormMeta(object):

    @classmethod
    def items_init(cls, value):
        items = []
        if type(value) is not list:
            raise CustomError(500, 200, 'items type is not list')
        for item in value:
            new_item = {'item_type_name': None,
                        'item_detail': None,
                        'using': True}
            for item_key, item_value in item.items():
                new_item[item_key] = item_value
            items.append(new_item)
        return items

    @classmethod
    def reformatter_insert(cls, data: dict = None):
        if data is None:
            raise CustomError(500, 200, 'insert data can not be none')
        new_data = {
            'meta': {'create_by': None},
            'name': None,
            'version': None,
            'using': True,
            'items': []
        }
        for key, value in data.items():
            if key == 'items':
                items = cls.items_init(value)
                value = items
            new_data[key] = value
        return new_data

    @classmethod
    def formatter_simple(cls, data):
        try:
            json_dict = {
                '_id': str(data.get('_id', None)),
                'version': data.get('version', None),
                'name': data.get('name', None),
                'meta': data.get('meta', {}),
            }
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return json_dict

    @classmethod
    def formatter_total(cls, data: dict):
        try:
            json_dict = {
                '_id': str(data.get('_id', None)),
                'version': data.get('version', None),
                'name': data.get('name', None),
                'meta': data.get('meta', {}),
                'items': data.get('items', [])
            }
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return json_dict

    @classmethod
    def get_form_meta(cls, name: str = None, version: str = None, unscoped: bool = False):
        from app.utils.mongodb import mongo
        if name is None:
            raise CustomError(500, 200, 'name must be given')
        condition = dict()
        if not unscoped:
            condition['using'] = True
        condition['name'] = name
        if version is not None:
            condition['version'] = version
        try:
            data = mongo.db.form_meta.find_one(condition)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if data is None:
            raise CustomError(404, 404, 'form meta not found')
        return cls.formatter_total(data)

    @classmethod
    def query_form_metas(cls, query_dict: dict = None, unscoped: bool = False):
        if query_dict is None:
            query_dict = dict()
        from app.utils.mongodb import mongo
        if not unscoped:
            query_dict['using'] = [True]
        url_condition = mongodb_url_condition.UrlCondition(query_dict)
        if len(url_condition.filter_dict) == 0:
            try:
                datas = mongo.db.form_meta.find()
            except Exception as e:
                raise (500, 500, str(e))
            return datas, datas.count()
        if '_id' in url_condition.filter_dict:
            url_condition.filter_dict['_id']['$in'] = [mongodb_url_condition.ObjectId(item) for item in
                                                       url_condition.filter_dict['_id']['$in']]
        try:
            datas = mongo.db.form_meta.find(url_condition.filter_dict)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        datas = mongodb_url_condition.sort_limit(datas, url_condition.sort_limit_dict)
        paginate = mongodb_url_condition.Paginate(datas, url_condition.page_dict)
        datas = paginate.data_page
        return [cls.formatter_simple(data) for data in datas], paginate.total

    @classmethod
    def insert_form_meta(cls, data: dict = None):
        if data is None:
            data = dict()
        from app.utils.mongodb import mongo
        if data is None:
            data = dict()
        data = cls.reformatter_insert(data)
        try:
            mongo.db.form_meta.insert(data)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def delete_form_meta(cls, where_dict: dict = None):
        from app.utils.mongodb import mongo
        if where_dict is None:
            raise CustomError(500, 500, 'condition can not be empty')
        where_dict['using'] = True
        try:
            mongo.db.form_meta.update(where_dict, {'$set': {'using': False}})
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return True


class WorkPlan(db.Model):
    __tablename__ = 'work_plans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    term = db.Column(db.String(20))
    form_meta_name = db.Column(db.String(20))
    form_meta_version = db.Column(db.String(20))
    status = db.Column(db.String(20))
    using = db.Column(db.Boolean, default=True)

    @classmethod
    def formatter(cls, work_plan):
        try:
            work_plan_dict = {
                'id': work_plan.id,
                'term': work_plan.term,
                'form_meta_name': work_plan.form_meta_name,
                'form_meta_version': work_plan.form_meta_version,
                'status': work_plan.status
            }
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return work_plan_dict

    @classmethod
    def reformatter_insert(cls, data: dict):
        return data

    @classmethod
    def reformatter_update(cls, data: dict):
        return data

    @classmethod
    def insert_work_plan(cls, ctx: bool = True, data: dict = None):
        if data is None:
            data = dict()
        data = cls.reformatter_insert(data)
        work_plan = WorkPlan()
        for key, value in data.items():
            if hasattr(work_plan, key):
                setattr(work_plan, key, value)
        db.session.add(work_plan)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def query_work_plan(cls, query_dict: dict = None, unscoped: bool = False):
        if query_dict is None:
            query_dict = dict()
        name_map = {'work_plans': WorkPlan}
        query = WorkPlan.query
        if not unscoped:
            query = query.filter(WorkPlan.using == True)
        url_condition = mysql_url_condition.UrlCondition(query_dict)
        try:
            (query, total) = mysql_url_condition.process_query(query, url_condition.filter_dict,
                                                               url_condition.sort_limit_dict, url_condition.page_dict,
                                                               name_map, WorkPlan)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return [cls.formatter(data) for data in query], total

    @classmethod
    def get_work_plan(cls, id: int, unscoped: bool = False):
        work_plan = WorkPlan.query
        if not unscoped:
            work_plan = work_plan.filter(WorkPlan.using == True)
        try:
            work_plan = work_plan.filter(WorkPlan.id == int(id)).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if work_plan is None:
            raise CustomError(404, 404, 'work plan not found')
        return cls.formatter(work_plan)

    @classmethod
    def delete_work_plan(cls, ctx: bool = True, query_dict: dict = None):
        if query_dict is None:
            query_dict = dict()
        name_map = {'work_plans': WorkPlan}
        work_plans = WorkPlan.query.filter(WorkPlan.using == True)
        url_condition = mysql_url_condition.UrlCondition(query_dict)
        try:
            (work_plans, total) = mysql_url_condition.process_query(work_plans, url_condition.filter_dict,
                                                                    url_condition.sort_limit_dict,
                                                                    url_condition.page_dict, name_map, WorkPlan)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for work_plan in work_plans:
            work_plan.using = False
            db.session.add(work_plan)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_work_plan(cls, ctx: bool = True, query_dict: dict = None, data: dict = None):
        if data is None:
            data = dict()
        if query_dict is None:
            query_dict = dict()
        data = cls.reformatter_update(data)
        name_map = {'work_plans': WorkPlan}
        work_plans = WorkPlan.query.filter(WorkPlan.using == True)
        url_condition = mysql_url_condition.UrlCondition(query_dict)
        try:
            (work_plans, total) = mysql_url_condition.process_query(work_plans, url_condition.filter_dict,
                                                                    url_condition.sort_limit_dict,
                                                                    url_condition.page_dict, name_map, WorkPlan)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for lesson_record in work_plans:
            for key, value in data.items():
                if hasattr(lesson_record, key):
                    setattr(lesson_record, key, value)
            db.session.add(lesson_record)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True


class Form(object):

    @classmethod
    def values_init(cls, value):
        values = []
        if type(value) is not list:
            raise CustomError(500, 200, 'value type is not list')
        for item in value:
            new_item = {
                'item_type': None,
                'item_name': None,
                'type': None,
                'value': None,
                'pyload': dict()
            }
            for item_key, item_value in item.items():
                new_item[item_key] = item_value
            values.append(new_item)
        return values

    @classmethod
    def reformatter_insert(cls, data: dict):
        new_data = {
            'bind_meta_id': None,
            'bind_meta_name': None,
            'bind_meta_version': None,
            'meta': {
                'create_at': None,
                'creator': {}
            },
            'status': None,
            'using': True,
            'values': []
        }
        for key, value in data.items():
            if key == 'values':
                values = cls.values_init(value)
                value = values
            new_data[key] = value
        return new_data

    @classmethod
    def formatter_simple(cls, data: dict):
        try:
            json_dict = {
                '_id': str(data.get('_id', None)),
                'meta': data.get('meta', {}),
                'status': data.get('status'),
                'bind_meta_id': data.get('bind_meta_id', None),
                'bind_meta_name': data.get('bind_meta_name', None),
                'bind_meta_version': data.get('bind_meta_version', None),
                'values': data.get('values', [])
            }
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return json_dict

    @classmethod
    def formatter_total(cls, data: dict):
        try:
            json_dict = {
                '_id': str(data.get('_id', None)),
                'meta': data.get('meta', {}),
                'status': data.get('status'),
                'bind_meta_id': data.get('bind_meta_id', None),
                'bind_meta_name': data.get('bind_meta_name', None),
                'bind_meta_version': data.get('bind_meta_version', None),
                'values': data.get('values', [])
            }
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return json_dict

    @classmethod
    def get_form(cls, _id=None, unscoped: bool = False):
        from app.utils.mongodb import mongo
        if _id is None:
            raise CustomError(500, 500, '_id must be given')
        condition = dict()
        if not unscoped:
            condition['using'] = True
        condition['_id'] = _id
        try:
            data = mongo.db.form.find_one(condition)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if data is None:
            raise CustomError(404, 404, 'form not found')
        return cls.formatter_total(data)

    @classmethod
    def query_forms(cls, query_dict: dict = None, unscoped: bool = False):
        from app.utils.mongodb import mongo
        if query_dict is None:
            query_dict = dict()
        if not unscoped:
            query_dict['using'] = [True]
        url_condition = mongodb_url_condition.UrlCondition(query_dict)
        if len(url_condition.filter_dict) == 0:
            try:
                datas = mongo.db.form.find()
            except Exception as e:
                raise CustomError(code=500, status_code=500, err_info=str(e))
            return datas, datas.count()
        if '_id' in url_condition.filter_dict:
            url_condition.filter_dict['_id']['$in'] = [mongodb_url_condition.ObjectId(item) for item in
                                                       url_condition.filter_dict['_id']['$in']]
        try:
            datas = mongo.db.form.find(url_condition.filter_dict)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        datas = mongodb_url_condition.sort_limit(datas, url_condition.sort_limit_dict)
        paginate = mongodb_url_condition.Paginate(datas, url_condition.page_dict)
        datas = paginate.data_page
        return [cls.formatter_simple(data=data) for data in datas], paginate.total

    @classmethod
    def insert_form(cls, data: dict = None):
        if data is None:
            data = dict()
        data = cls.reformatter_insert(data)
        from app.utils.mongodb import mongo
        if data is None:
            data = dict()
        try:
            mongo.db.form.insert(data)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def delete_form(cls, where_dict: dict = None):
        from app.utils.mongodb import mongo
        if where_dict is None:
            raise CustomError(500, 500, 'condition can not be None')
        try:
            mongo.db.form.update(where_dict, {'$set': {'using': False}})
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_form(cls, where_dict: dict = None, data: dict = None):
        if data is None:
            data = dict()
        from app.utils.mongodb import mongo
        if where_dict is None:
            condition = dict()
            condition['using'] = True
        if data is None:
            raise CustomError(200, 500, 'change data can not be None')
        try:
            mongo.db.form.update(where_dict, {'$set': data})
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return True
