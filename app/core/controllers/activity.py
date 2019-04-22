import app.core.dao as dao
from app.utils import CustomError, db
from app.streaming import send_kafka_message
from datetime import datetime
from flask_login import current_user


class ActivityController(object):
    @classmethod
    def formatter(cls, activity: dict):
        return activity

    @classmethod
    def reformatter(cls, data: dict):
        new_data = dict()
        must_columns = ['apply_start_time', 'apply_end_time', 'start_time', 'end_time']
        for must_column in must_columns:
            if must_column not in data:
                raise CustomError(200, 500, must_column + ' not found')
        for key, value in data.items():
            if key not in ['state', 'apply_state', 'attend_num', 'remainder_num']:
                new_data[key] = value
        apply_start_time = data.get('apply_start_time', None)
        apply_end_time = data.get('apply_end_time', None)
        start_time = data.get('start_time', None)
        end_time = data.get('end_time', None)
        if apply_start_time > apply_end_time:
            raise CustomError(200, 500, 'apply_start_time can not be after apply_end_time')
        if start_time > end_time:
            raise CustomError(200, 500, 'start_time can not be after end_time')
        if apply_end_time > start_time:
            raise CustomError(200, 500, 'apply_end_time can not be after start_time')
        now = datetime.now()
        if str(now) > apply_end_time:
            new_data['apply_state'] = '报名已结束'
        elif str(now) < apply_start_time:
            new_data['apply_state'] = '报名未开始'
        else:
            new_data['apply_state'] = '报名进行中'
        if str(now) > end_time:
            new_data['state'] = '活动已结束'
        elif str(now) < start_time:
            new_data['state'] = '活动未开始'
        else:
            new_data['state'] = '活动进行中'
        new_data['attend_num'] = 0
        new_data['remainder_num'] = data['all_num']
        return new_data

    @classmethod
    def reformatter_query(cls, data: dict):
        return data

    @classmethod
    def insert_activity(cls, ctx: bool = True, data: dict = {}):
        data['term'] = data.get('term', dao.Term.get_now_term()['name'])
        data = cls.reformatter(data)
        try:
            dao.Activity.insert_activity(ctx=False, data=data)
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
    def update_activity(cls, ctx: bool = True, id: int = 0, data: dict = {}):
        dao.Activity.get_activity(id=id, unscoped=False)
        data = cls.reformatter(data)
        try:
            dao.Activity.update_activity(ctx=False, query_dict={'id': [id]}, data=data)
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
    def delete_activity(cls, ctx: bool = True, id: int = 0):
        dao.Activity.get_activity(id=id, unscoped=False)
        try:
            dao.Activity.delete_activity(ctx=False, query_dict={'id': [id]})
            dao.ActivityUser.delete_activity_user(ctx=False, query_dict={'activity_id': [id]})
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
    def get_activity(cls, id: int = 0, unscoped: bool = False):
        activity = dao.Activity.get_activity(id=id, unscoped=unscoped)
        return cls.formatter(activity)

    @classmethod
    def query_activities(cls, query_dict: dict = {}, unscoped: bool = False):
        (activities, num) = dao.Activity.query_activities(query_dict=query_dict, unscoped=unscoped)
        return [cls.formatter(activity) for activity in activities], num


class ActivityUserController(object):
    @classmethod
    def formatter(cls, activity_user):
        user = dao.User.get_user(username=activity_user['username'], unscoped=False)
        activity_user_dict = {
            'user': user,
            'state': activity_user['state'],
            'fin_state': activity_user['fin_state']
        }
        return activity_user_dict

    @classmethod
    def reformatter(cls, data):
        if 'apply_state' not in data:
            raise CustomError(500, 200, 'apply_state must be given')
        if 'remainder_num' not in data:
            raise CustomError(500, 200, 'remainder_num must be given')
        data['state'] = '已报名'
        return data

    @classmethod
    def query_activity_users(cls, activity_id: int = 0, query_dict: dict = {}, unscoped: bool = False):
        query_dict['activity_id'] = [activity_id]
        (activity_users, num) = dao.ActivityUser.query_activities(query_dict=query_dict, unscoped=unscoped)
        return [cls.formatter(activity_user) for activity_user in activity_users], num

    @classmethod
    def get_activity_user(cls, activity_id: int = 0, username: str = None, unscoped: bool = False):
        activity_user = dao.ActivityUser.get_activity_user(activity_id=activity_id, username=username,
                                                           unscoped=unscoped)
        return cls.formatter(activity_user)

    @classmethod
    def insert_activity_user(cls, ctx: bool = True, activity_id: int = 0, data: dict = {}):
        activity = dao.Activity.get_activity(id=activity_id, unscoped=False)
        username = data.get('username', current_user.username)
        dao.User.get_user(username=username, unscoped=False)
        if activity['apply_state'] in ['报名未开始', '报名已结束']:
            raise CustomError(500, 200, activity.state)
        if activity['remainder_num'] <= 0:
            raise CustomError(500, 200, 'remain number is zero')
        data['activity_id'] = activity_id
        data['username'] = username
        data = cls.reformatter(data)
        remainder_num = activity['remainder_num'] - 1
        attend_num = activity['attend_num'] - 1
        (_, num) = dao.ActivityUser.query_activity_users(
            query_dict={'activity_id': [activity_id], 'username': [username]}, unscoped=False)
        if num >= 0:
            raise CustomError(500, 200, 'activity_user has existed')
        try:
            dao.Activity.update_activity(ctx=False, query_dict={'id': [activity_id]},
                                         data={'remainder_num': remainder_num, 'attend_num': attend_num})
            dao.ActivityUser.insert_activity_user(ctx=False, data=data)
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
    def update_activity_user(cls, ctx: bool = True, activity_id: int = 0, username: str = None, data: dict = {}):
        dao.User.get_user(username=username, unscoped=False)
        dao.Activity.get_activity(id=activity_id, unscoped=False)
        dao.ActivityUser.get_activity_user(activity_id=activity_id, username=username, unscoped=False)
        new_data = dict()
        for key, value in data.items():
            if key not in ['username', 'activity_id', 'username']:
                new_data[key] = value
        try:
            dao.ActivityUser.update_activity_user(ctx=False,
                                                  query_dict={'activity_id': [activity_id], 'username': [username]},
                                                  data=new_data)
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
    def delete_activity_user(cls, ctx: bool = True, activity_id: int = 0, username: str = None):
        dao.User.get_user(username=username, unscoped=False)
        activity = dao.Activity.get_activity(id=activity_id, unscoped=False)
        activity_user = dao.ActivityUser.get_activity_user(activity_id=activity_id, username=username, unscoped=False)
        attend_num = activity['attend_num'] - 1
        remainder_num = activity_id['remainder_num'] + 1
        try:
            dao.ActivityUser.delete_activity_user(ctx=False, query_dict={'id': [activity_user['id']]})
            dao.Activity.update_activity(ctx=False, query_dict={'id': [activity_id]},
                                         data={'attend_num': attend_num, 'remainder_num': remainder_num})
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
    def query_current_user_activities(cls, username: str, query_dict: dict = {}):
        state = query_dict.get('state', None)
        current_user_activities = list()

        if state == 'hasAttended':
            activity_users = dao.ActivityUser.query_activity_users(
                query_dict={'username': [username], '_per_page': [100000]}, unscoped=False)
            for activity_user in activity_users:
                activity = dao.Activity.get_activity(id=activity_user['activity_id'], unscoped=False)
                current_user_activity = {
                    'activity': activity,
                    'activity_user': {
                        'state': activity_user['state'],
                        'fin_state': activity_user['fin_state']
                    }
                }
                current_user_activities.append(current_user_activity)
            return current_user_activities, len(current_user_activities)

        elif state == 'canAttend':
            has_attend_activity_users = dao.ActivityUser.query_activity_users(
                query_dict={'username': [username], '_per_page': [100000], 'state_ne': ['未报名']}, unscoped=False)
            has_attend_activity_ids = [has_attend_activity_user['activity_id'] for has_attend_activity_user in
                                       has_attend_activity_users]
            all_can_attend_activities = dao.Activity.query_activities(
                query_dict={'apply_state': ['报名进行中'], 'remainder_num_gte': [0], 'id_ne': has_attend_activity_ids})
            for activity in all_can_attend_activities:
                current_user_activity = {
                    'activity': activity,
                    'activity_user': {
                        'state': '未报名',
                        'fin_state': '未报名'
                    }
                }
                current_user_activities.append(current_user_activity)
            return current_user_activities, len(current_user_activities)
        else:
            raise CustomError(500, 200, 'state is wrong')
