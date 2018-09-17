from app.core.models.lesson import ModelLesson
from app.utils.mysql import db


def insert_model_lesson(request_json):
    model_lesson = ModelLesson()
    for key, value in request_json.items():
        if hasattr(model_lesson, key):
            setattr(model_lesson, key, value)
    db.session.add(model_lesson)
    try:
        db.session.commit()
    except Exception as e:
        return False, e
    return True, None