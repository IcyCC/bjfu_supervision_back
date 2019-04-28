from flask_login import UserMixin, AnonymousUserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.mysql import db
from app import login_manager
from datetime import datetime
from flask import jsonify
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from app.utils.url_condition.url_condition_mysql import UrlCondition, process_query, count_query
from app.utils.Error import CustomError


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    username = db.Column(db.String(64), index=True, default='')
    name = db.Column(db.String(64), default='')
    password_hash = db.Column(db.String(128), default='')
    sex = db.Column(db.String(16), default='男')
    email = db.Column(db.String(64), default='')
    phone = db.Column(db.String(16), default='')
    state = db.Column(db.String(8), default='')
    unit = db.Column(db.String(8), default='')
    status = db.Column(db.String(8), default='')
    prorank = db.Column(db.String(8), default='')
    skill = db.Column(db.String(16), default='')
    using = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    leader = db.Column(db.Boolean, default=False)
    guider = db.Column(db.Boolean, default=False)

    @classmethod
    def formatter(cls, user):
        user_dict = {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'sex': user.sex,
            'email': user.email,
            'phone': user.phone,
            'state': user.state,
            'unit': user.unit,
            'status': user.status,
            'prorank': user.prorank,
            'skill': user.skill,
            'is_guider': user.guider,
            'is_leader': user.leader,
            'is_admin': user.admin
        }
        return user_dict

    @classmethod
    def reformatter_update(cls, data: dict):
        allow_change_list = ['name', 'sex', 'password', 'email', 'phone', 'state', 'unit', 'status', 'prorank',
                             'skill', 'group', 'work_state', 'term', 'admin', 'leader', 'guider']
        update_data = dict()
        for key, value in data.items():
            if key in allow_change_list:
                update_data[key] = value
        return update_data

    @classmethod
    def reformatter_insert(cls, data: dict):
        return data

    @classmethod
    def count(cls, query_dict: dict, unscoped: bool = False):
        if query_dict is None:
            query_dict = {}
        name_map = {'users': User}
        query = User.query
        if not unscoped:
            query = query.filter(User.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            total = count_query(query, url_condition.filter_dict, url_condition.sort_limit_dict, name_map, User)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return total

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def login(cls, username: str, password: str):
        user = User.query.filter(User.username == username).filter(User.using == True).first()
        if user is None or not check_password_hash(user.password_hash, password):
            raise CustomError(401, 401, 'username or password may be wrong')
        login_user(user, remember=False)

    @classmethod
    def logout(cls):
        logout_user()

    @classmethod
    def get_user(cls, username: str, unscoped=False):
        user = User.query
        if not unscoped:
            user = user.filter(User.using == True)
        try:
            user = user.filter(User.username == username).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if user is None:
            raise CustomError(404, 404, 'user not found')
        return cls.formatter(user)

    @classmethod
    def query_users(cls, query_dict: dict = None, unscoped=False):
        if query_dict is None:
            query_dict = {}
        name_map = {'users': User, 'groups': Group}
        query = User.query
        if not unscoped:
            query = query.filter(User.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (query, total) = process_query(query, url_condition.filter_dict,
                                           url_condition.sort_limit_dict, url_condition.page_dict,
                                           name_map, User)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return [cls.formatter(data) for data in query], total

    @classmethod
    def insert_user(cls, ctx=True, data=None):
        if data is None:
            raise CustomError(500, 200, 'data must be given')
        data = cls.reformatter_insert(data)
        user = User()
        for key, value in data.items():
            if key == 'password':
                user.password = value
            if hasattr(user, key):
                setattr(user, key, value)
        role_names = data.get('role_names', [])
        role_name_dict = {'教师': 'teacher', '管理员': 'admin', '领导': 'leader'}
        for role_name in role_names:
            role_name_e = role_name_dict[role_name]
            if hasattr(user, role_name_e):
                setattr(user, role_name_e, True)
        db.session.add(user)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def delete_user(cls, ctx=True, username: str = None):
        try:
            user = User.query.filter(User.username == username).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if user is None:
            raise CustomError(404, 404, 'user not found')
        user.using = False
        db.session.add(user)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_user(cls, ctx=True, username: str = None, data: dict = None):
        if data is None:
            data = {}
        data = cls.reformatter_update(data)
        try:
            user = User.query.filter(User.username == username).filter(User.using == True).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if user is None:
            raise CustomError(404, 404, 'user not found')
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.session.add(user)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise CustomError(500, 500, str(e))
        return True


login_manager.anonymous_user = AnonymousUserMixin


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    name = db.Column(db.String(64), unique=True, default='')
    leader_name = db.Column(db.String(64), default='')
    using = db.Column(db.Boolean, default=True)

    @classmethod
    def formatter(cls, group):
        group_dict = {
            'name': group.name,
            'leader_name': group.leader_name
        }
        return group_dict

    @classmethod
    def count(cls, query_dict: dict, unscoped: bool = False):
        if query_dict is None:
            query_dict = {}
        name_map = {'groups': Group}
        query = Group.query
        if not unscoped:
            query = query.filter(Group.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            total = count_query(query, url_condition.filter_dict, url_condition.sort_limit_dict, name_map, Group)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return total

    @classmethod
    def get_group(cls, group_name: str):
        try:
            group = Group.query.filter(Group.using == True).filter(Group.name == group_name).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if group is None:
            raise CustomError(404, 404, 'group not found')
        return cls.formatter(group)

    @classmethod
    def query_groups(cls, query_dict: dict = None):
        if query_dict is None:
            query_dict = {}
        name_map = {'groups': Group}
        url_condition = UrlCondition(query_dict)
        query = Group.query.filter(Group.using == True)
        try:
            (query, total) = process_query(query, url_condition.filter_dict,
                                           url_condition.sort_limit_dict, url_condition.page_dict,
                                           name_map, Group)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return [cls.formatter(data) for data in query], total

    @classmethod
    def update_group(cls, ctx=True, query_dict: dict = None, data: dict = None):
        if data is None:
            data = {}
        if query_dict is None:
            query_dict = {}
        name_map = {'groups': Group}
        url_condition = UrlCondition(query_dict)
        groups = Group.query.filter(Group.using == True)
        try:
            (groups, total) = process_query(groups, url_condition.filter_dict,
                                            url_condition.sort_limit_dict, url_condition.page_dict,
                                            name_map, Group)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for group in groups:
            for key, value in data.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            db.session.add(group)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise CustomError(500, 500, str(e))
        return True


class Supervisor(db.Model):
    __tablename__ = 'supervisors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    username = db.Column(db.String(64), default='')
    name = db.Column(db.String(64), default='')
    group = db.Column(db.String(16), default='')
    work_state = db.Column(db.String(8), default='')
    term = db.Column(db.String(32), default='')
    using = db.Column(db.Boolean, default=True)
    grouper = db.Column(db.Boolean, default=False)
    main_grouper = db.Column(db.Boolean, default=False)

    @classmethod
    def formatter(cls, supervisor):
        supervisor_dict = {
            'group': supervisor.group,
            'username': supervisor.username,
            'is_grouper': supervisor.grouper,
            'is_main_grouper': supervisor.main_grouper,
            'work_state': supervisor.work_state,
            'term': supervisor.term
        }
        return supervisor_dict

    @classmethod
    def count(cls, query_dict: dict, unscoped: bool = False):
        if query_dict is None:
            query_dict = {}
        name_map = {'supervisors': Supervisor}
        query = Supervisor.query
        if not unscoped:
            query = query.filter(Supervisor.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            total = count_query(query, url_condition.filter_dict, url_condition.sort_limit_dict, name_map, Supervisor)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return total

    @classmethod
    def query_supervisors(cls, query_dict: dict, unscoped: bool = False):
        name_map = {'supervisors': Supervisor, 'users': User}
        supervisors = Supervisor.query
        if not unscoped:
            supervisors = supervisors.filter(Supervisor.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (supervisors, total) = process_query(supervisors, url_condition.filter_dict,
                                                 url_condition.sort_limit_dict, url_condition.page_dict,
                                                 name_map, Supervisor)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return [cls.formatter(supervisor) for supervisor in supervisors], total

    @classmethod
    def get_supervisor(cls, username: str = None, term: str = None, unscoped: bool = False):
        supervisor = Supervisor.query
        if not unscoped:
            supervisor = supervisor.filter(Supervisor.using == True)
        try:
            supervisor = supervisor.filter(Supervisor.username == username).filter(Supervisor.term == term).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if supervisor is None:
            raise CustomError(404, 404, 'user not found')
        return cls.formatter(supervisor)

    @classmethod
    def get_supervisor_by_id(cls, id: int, unscoped: bool = False):
        supervisor = Supervisor.query
        if not unscoped:
            supervisor = supervisor.filter(Supervisor.using == True)
        try:
            supervisor = supervisor.filter(Supervisor.username == id).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if supervisor is None:
            raise CustomError(404, 404, 'user not found')
        return cls.formatter(supervisor)

    @classmethod
    def insert_supervisor(cls, ctx=True, data=None):
        supervisor = Supervisor()
        for key, value in data.items():
            if hasattr(supervisor, key):
                setattr(supervisor, key, value)
        db.session.add(supervisor)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def delete_supervisor(cls, ctx: bool = True, query_dict: dict = None):
        if query_dict is None:
            query_dict = {}
        name_map = {'supervisors': Supervisor}
        query = Supervisor.query.filter(Supervisor.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (supervisors, total) = process_query(query, url_condition.filter_dict,
                                                 url_condition.sort_limit_dict, url_condition.page_dict,
                                                 name_map, Supervisor)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for supervisor in supervisors:
            supervisor.using = False
            db.session.add(supervisor)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_supervisor(cls, ctx: bool = True, query_dict: dict = None, data: dict = None):
        if data is None:
            data = {}
        if query_dict is None:
            query_dict = {}
        name_map = {'supervisors': Supervisor}
        query = Supervisor.query.filter(Supervisor.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (supervisors, total) = process_query(query, url_condition.filter_dict,
                                                 url_condition.sort_limit_dict, url_condition.page_dict,
                                                 name_map, Supervisor)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for supervisor in supervisors:
            for key, value in data.items():
                if hasattr(supervisor, key):
                    setattr(supervisor, key, value)
            db.session.add(supervisor)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    name = db.Column(db.String(255), default='')
    username = db.Column(db.String(64), default='')
    detail = db.Column(db.String(1023), default='')
    timestamp = db.Column(db.TIMESTAMP, default=datetime.now)
    using = db.Column(db.Boolean, default=True)

    @classmethod
    def formatter(cls, event):
        event_dict = {
            'id': event.id,
            'username': event.username,
            'detail': event.detail,
            'timestamp': str(event.timestamp),
            'using': event.using
        }
        return event_dict

    @classmethod
    def reformatter_insert(cls, data: dict):
        return data

    @classmethod
    def reformatter_update(cls, data: dict):
        return data

    @classmethod
    def count(cls, query_dict: dict, unscoped: bool = False):
        if query_dict is None:
            query_dict = {}
        name_map = {'events': Event}
        query = Event.query
        if not unscoped:
            query = query.filter(Event.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            total = count_query(query, url_condition.filter_dict, url_condition.sort_limit_dict, name_map, Event)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return total

    @classmethod
    def get_event(cls, id: int, unscoped: bool = False):
        event = Event.query
        if not unscoped:
            event = event.filter(Event.using == True)
        try:
            event = event.filter(Event.id == id).filter(Event.using == True).first()
        except Exception as e:
            raise CustomError(500, 500, str(e))
        if event is None:
            raise CustomError(404, 404, 'event not found')
        return cls.formatter(event)

    @classmethod
    def insert_event(cls, ctx: bool = True, data: dict = None):
        if data is None:
            data = {}
        data = cls.reformatter_insert(data)
        event = Event()
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        db.session.add(event)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def query_events(cls, query_dict: dict = None, unscoped: bool = False):
        if query_dict is None:
            query_dict = {}
        name_map = {'events': Event}
        query = Event.query
        if not unscoped:
            query = query.filter(Event.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (query, total) = process_query(query, url_condition.filter_dict, url_condition.sort_limit_dict,
                                           url_condition.page_dict, name_map, Event)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        return [cls.formatter(data) for data in query], total

    @classmethod
    def delete_event(cls, ctx: bool = True, query_dict: dict = None):
        if query_dict is None:
            query_dict = {}
        name_map = {'events': Event}
        events = Event.query.filter(Event.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (events, total) = process_query(events, url_condition.filter_dict,
                                            url_condition.sort_limit_dict,
                                            url_condition.page_dict, name_map, Event)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for event in events:
            event.using = False
            db.session.add(event)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True

    @classmethod
    def update_event(cls, ctx: bool = True, query_dict: dict = None, data: dict = None):
        if data is None:
            data = {}
        if query_dict is None:
            query_dict = {}
        data = cls.reformatter_update(data)
        name_map = {'events': Event}
        events = Event.query.filter(Event.using == True)
        url_condition = UrlCondition(query_dict)
        try:
            (events, total) = process_query(events, url_condition.filter_dict,
                                            url_condition.sort_limit_dict,
                                            url_condition.page_dict, name_map, Event)
        except Exception as e:
            raise CustomError(500, 500, str(e))
        for event in events:
            for key, value in data.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            db.session.add(event)
        if ctx:
            try:
                db.session.commit()
            except Exception as e:
                raise CustomError(500, 500, str(e))
        return True


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                return jsonify(status='fail', data=[], reason='no permission')
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
