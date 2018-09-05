from app.http.handler.block_type import block_type_blueprint
from flask_pymongo import ObjectId
from flask import jsonify, request
from app.core.controllers.block_type_controller import insert_block_type, delete_block_type, find_block_type, \
    update_block_type, request_to_class, request_to_change, find_block_types
from app.core.controllers.common_controller import dict_serializable, UrlCondition, sort_limit, Paginate, object_to_str


@block_type_blueprint.route('/block_types')
def get_block_types():
    url_condition = UrlCondition(request.args)
    from run import mongo
    (block_types, err) = find_block_types(mongo, url_condition.filter_dict)
    if err is not None:
        return jsonify({
            'code': 500,
            'message': str(err),
            'total': 0,
            'block_types': []
        }), 500
    block_types = sort_limit(block_types, url_condition.sort_limit_dict)
    paginate = Paginate(block_types, url_condition.page_dict)
    return jsonify({
        'code': 200,
        'message': '',
        'block_types': [object_to_str(block_type) for block_type in block_types],
        'total': paginate.total,
    }), 200


@block_type_blueprint.route('/block_types', methods=['POST'])
def new_block_type():
    from run import mongo
    block_type = request_to_class(request.json)
    (ifSuccess, err) = insert_block_type(mongo, block_type)
    if err is not None:
        return jsonify({
            'code': 500,
            'message': str(err),
            'block_type': None
        }), 500
    return jsonify({
        'code': 200,
        'message': '',
        'block_type': None
    }), 200


@block_type_blueprint.route('/block_types/<string:_id>')
def get_block_type(_id):
    from run import mongo
    (block_type, err) = find_block_type(mongo, _id)
    if err is not None:
        return jsonify({
            'code': 500,
            'message': str(err),
            'block_type': None
        }), 500
    if block_type is None:
        return jsonify({
            'code': 404,
            'message': '',
            'block_type': None
        }), 404
    return jsonify({
        'code': 200,
        'message': '',
        'block_type': object_to_str(block_type) if block_type is not None else None
    }), 200


@block_type_blueprint.route('/block_types/<string:_id>', methods=['DELETE'])
def del_block_type(_id):
    from run import mongo
    (block_type, err) = find_block_type(mongo, _id)
    if err is not None:
        return jsonify({
            'code': 500,
            'message': str(err),
            'block_type': None
        }), 500
    if block_type is None:
        return jsonify({
            'code': 404,
            'message': 'Not found',
            'block_type': None
        }), 404
    (_, err) = delete_block_type(mongo, {'_id': ObjectId(_id)})
    if err is not None:
        return jsonify({
            'code': 500,
            'message': str(err),
            'block_type': None
        }), 500
    return jsonify({
        'code': 200,
        'message': '',
        'block_type': None
    }), 200


@block_type_blueprint.route('/block_types/<string:_id>', methods=['PUT'])
def change_block_type(_id):
    from run import mongo
    (block_type, err) = find_block_type(mongo, _id)
    if err is not None:
        return jsonify({
            'code':500,
            'message':str(err),
            'block_type':None
        }),500
    if block_type is None:
        return jsonify({
            'code': 404,
            'message': 'no this block_type',
            'block_type': None
        }), 404
    change = request_to_change(request.json)
    (_, err) = update_block_type(mongo, {'_id': ObjectId(_id)}, change)
    if err is not None:
        return jsonify({
            'code':500,
            'message':str(err),
            'block_type':None
        }),500
    return jsonify({
        'code': 200,
        'message': '',
        'block_type': None
    }), 200
