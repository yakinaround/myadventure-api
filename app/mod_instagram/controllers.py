"""
controllers.py

Instagram module controllers.
"""
from flask import Response, Blueprint
import json
import hashlib
import logging
import urlparse
import bson
from instagram.client import InstagramAPI

from app.mod_point.models import Point
from app.mod_config.models import Config
from app.mod_auth import oauth

api = None

mod_instagram = Blueprint('instagram', __name__, url_prefix='/api/v1/instagram')


def get_media(media=None, max_id=None):

    if media is None:
        media = []

    response, next = api.user_recent_media(max_id=max_id)

    for media_item in response:
        media.append(media_item)

    if next is not None:
        parsednext = urlparse.urlparse(next)
        max_id = urlparse.parse_qs(parsednext.query)['max_id'][0]
        media = get_media(media, max_id)

    return media


def import_media(access_token, client_secret):

    global api
    api = InstagramAPI(access_token=access_token.encode('ascii', 'ignore'), client_secret=client_secret.encode('ascii', 'ignore'))

    m = hashlib.md5()

    media = get_media()

    for item in media:

        pointid = int(m.hexdigest()[:8], 16)

        point = Point.objects(pointid == pointid).first()

        if point is None:

            m.update(item.id)

            title = None
            desc = None
            video = None
            if hasattr(item, 'caption'):
                if item.caption is not None:
                    desc = item.caption.text
            if hasattr(item, 'location'):
                if item.location.name is not None:
                    title = item.location.name
                if item.location.point is not None:
                    latitude = item.location.point.latitude
                    longitude = item.location.point.longitude
            timestamp = item.created_time
            thumb = item.images.get('thumbnail').url
            photo = item.images.get('standard_resolution').url
            if hasattr(item, 'videos'):
                video = item.videos.get('standard_resolution').url
            resource = item.link

            try:
                point = Point(
                    title=title,
                    latitude=latitude,
                    longitude=longitude,
                    type='photo',
                    timestamp=timestamp,
                    pointid=pointid,
                    thumb=thumb,
                    photo=photo,
                    video=video,
                    resource=resource,
                    desc=desc
                )
                point.save()
            except AttributeError:
                pass
            except Exception as e:
                logging.error(e.args[0])

    return Response(json.dumps({'status': 'ok'}), status=200, mimetype='application/json')


@mod_instagram.route('/load', methods=['GET'])
@oauth.require_oauth('email')
def load_instagram():
    access_token = Config.objects(name='instagram_access_token').order_by('-date_added').first()

    if access_token is None:
        return Response(bson.json_util.dumps({'error': 'instagram_access_token configuration was not found.'}), status=500, mimetype='application/json')

    client_secret = Config.objects(name='instagram_client_secret').order_by('-date_added').first()

    if client_secret is None:
        return Response(bson.json_util.dumps({'error': 'instagram_client_secret configuration was not found.'}), status=500, mimetype='application/json')

    return import_media(access_token.value, client_secret.value)
