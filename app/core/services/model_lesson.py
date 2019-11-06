'''
@Author: your name
@Date: 2019-11-06 17:19:25
@LastEditTime: 2019-11-06 20:00:43
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: /bjfu_supervision_back_ykx/app/core/services/model_lesson.py
'''
import json
from collections import Counter
from app import redis_cli
from app.core import dao

class ModelLessonService:

    @classmethod
    def refresh_vote_nums(cls, lesson_id):
        """刷新认同次数
        
        Arguments:
            lesson_id {[type]} -- [description]
        """
        forms_vote, num_vote = dao.Form.query_forms(
            query_dict= {
                "meta.lesson.lesson_id": lesson_id,
                "model_lesson.is_model_lesson": True,
                "status": "已完成"
            }
        )
        print("num_vote ", num_vote)
        dao.ModelLesson.update_model_lesson(
            query_dict={
            'lesson_id': lesson_id
            }, 
            data={
                "votes": num_vote
            }
        )
