"""
controllers.py

Adventure module controllers.
"""
import logging
from flask import Blueprint, jsonify, request, abort
from mongoengine import DoesNotExist
from werkzeug.exceptions import BadRequest
from slugify import slugify

from app.mod_adventure.models import Adventure
from app.mod_auth.controllers import oauth
from app.decorators import crossdomain

MOD_ADVENTURE = Blueprint('adventure', __name__, url_prefix='/api/v1/adventure')


@MOD_ADVENTURE.route('/', methods=['GET'])
@crossdomain(origin='*')
def list_adventures():
    adventures = Adventure.objects()
    adventures_dict = []
    for adventure in adventures:
        adventures_dict.append(adventure.to_dict())
    return jsonify(adventures=adventures_dict)


@MOD_ADVENTURE.route('/me', methods=['GET'])
@crossdomain(origin='*')
@oauth.require_oauth('email')
def list_user_adventures():
    user = request.oauth.user
    adventures = Adventure.objects(users=user)
    adventures_dict = []
    for adventure in adventures:
        adventures_dict.append(adventure.to_dict())
    return jsonify(adventures=adventures_dict)


@MOD_ADVENTURE.route('/<slug>', methods=['GET'])
@crossdomain(origin='*')
def get_adventure(slug):
    try:
        adventure = Adventure.objects.get(slug=slug)
        return jsonify(adventure.to_mongo())
    except DoesNotExist:
        abort(404)
    except Exception as e:
        logging.error(e)
        abort(500)
    return


@MOD_ADVENTURE.route('/', methods=['POST'])
@crossdomain(origin='*')
@oauth.require_oauth('email')
def add_adventure():
    try:
        name = request.values.get('name', None)
        user = request.oauth.user
        adventure = Adventure(
            slug=slugify(name),
            name=name,
            users=[user]
        )
        adventure.save()

        return jsonify(adventure.to_mongo())
    except TypeError as e:
        logging.error(e)
        abort(400)
    except BadRequest:
        abort(400)
    except Exception as e:
        logging.error(e)
        abort(500)
    return


@MOD_ADVENTURE.route('/<slug>', methods=['DELETE'])
@crossdomain(origin='*')
@oauth.require_oauth('email')
def delete_point(slug):
    adventure = Adventure.objects.get(slug=slug)
    try:
        adventure.delete()
        return jsonify(adventure.to_mongo())
    except DoesNotExist:
        abort(404)
    except Exception as e:
        logging.error(e)
        abort(500)
    return
