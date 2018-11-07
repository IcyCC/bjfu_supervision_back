from app.core.models.user import User, Supervisor
from app.core.models.lesson import Term, SchoolTerm
from app.utils.mysql import db
from app.utils.Error import CustomError


def get_supervisor(username=None, term=None):
    try:
        term = term if term is not None else Term.query.order_by(
            Term.name.desc()).filter(Term.using == True).first().name
    except Exception as e:
        return None, CustomError(500, 500, str(e))
    try:
        supervisor = Supervisor.query.filter(Supervisor.username == username).filter(Supervisor.term == term).filter(
            Supervisor.using == True).first()
    except Exception as e:
        return None, CustomError(500, 500, str(e))
    if supervisor is None:
        return None, CustomError(404, 404, 'supervisor not found')
    try:
        user = User.filter(User.username).filter(User.using == True).first()
    except Exception as e:
        return None, CustomError(500, 500, str(e))
    if user is None:
        return None, CustomError(404, 404, 'user not found')
    return user, None


def get_supervisors(condition=None):
    try:
        term = condition['term'] if condition is not None and 'term' in condition else Term.query.order_by(
            Term.name.desc()).filter(Term.using == True).first().name
        supervisors = Supervisor.query.filter(Supervisor.term == term).filter(Supervisor.using == True)
    except Exception as e:
        return None, CustomError(500, 500, str(e))
    page = int(condition['_page']) if '_page' in condition else 1
    per_page = int(condition['_per_page']) if '_per_page' in condition else 20
    pagination = supervisors.paginate(page=int(page), per_page=int(per_page), error_out=False)
    return pagination.items, pagination.total, None


def get_supervisors_expire(condition=None):
    try:
        term = condition['term'] if condition is not None and 'term' in condition else Term.query.order_by(
            Term.name.desc()).filter(Term.using == True).first().name
    except Exception as e:
        return None, None, CustomError(500, 500, str(e))
    new_term = (SchoolTerm(term) + 1).term_name
    try:
        all_usernames = [supervisor.username for supervisor in
                         Supervisor.query.filter(Supervisor.term == term).filter(Supervisor.using == True)]
        can_usernames = [supervisor.username for supervisor in
                         Supervisor.query.filter(Supervisor.term == new_term).filter(Supervisor.using == True)]
        expire_usernames = list(set(all_usernames) - set(can_usernames))
    except Exception as e:
        return None, None, CustomError(500, 500, str(e))
    try:
        users = User.query.filter(User.username.in_(expire_usernames))
        for key, value in condition.items():
            if hasattr(User, key):
                users = users.filter(getattr(User, key) == value)
    except Exception as e:
        return None, None, CustomError(500, 500, str(e))
    page = int(condition['_page']) if '_page' in condition else 1
    per_page = int(condition['_per_page']) if '_per_page' in condition else 20
    pagination = users.paginate(page=int(page), per_page=int(per_page), error_out=False)
    return pagination.items, pagination.total, None


def insert_supervisor(request_json):
    username = request_json.get('username', None)
    if username is None:
        return False, CustomError(500, 200, 'username must be given')
    supervisor = Supervisor()
    for key, value in request_json.items():
        if hasattr(supervisor, key):
            setattr(supervisor, key, value)
    db.session.add(supervisor)
    try:
        db.session.commit()
    except Exception as e:
        return False, CustomError(500, 500, str(e))
    return True, None
