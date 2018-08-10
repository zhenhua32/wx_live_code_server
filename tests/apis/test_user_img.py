import pytest
import qrcode
from io import BytesIO
from aiohttp import web
from multidict import MultiDict
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from livecode.middleware import parse_content, get_openid
from livecode.apis.login import get_empty_user
from livecode.apis.user_img import UserImg
from livecode.db import init_motor, init_resource, init_gridfs_resource
from tests.help import config, get_img


host = config['mongodb']['host']
port = config['mongodb']['port']
client = MongoClient(host, port)
db = client.live_code
fs_live_code_img = GridFS(db, 'live_code_img')
fs_user_img = GridFS(db, 'user_img')


@pytest.fixture
def cli(loop, aiohttp_client):
    app = web.Application(middlewares=[parse_content, get_openid])

    app['config'] = config
    app.on_startup.append(init_motor)
    app.on_startup.append(init_gridfs_resource)
    app.cleanup_ctx.append(init_resource)

    app.router.add_view('/wx/user/img', UserImg)

    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture(scope='function')
def user():
    one = get_empty_user()
    one['open_id'] = 'test_user_img'
    db.users.insert_one(one)

    result = db.live_code.insert_one({
        'open_id': 'test_user_img',
        'img': {}
    })
    live_code_id = str(result.inserted_id)
    yield {'session_id': one['open_id'], 'live_code_id': live_code_id}
    client.drop_database(db)


class TestUserImg:
    async def test_case_1(self, cli, user):
        data = {
            'live_code_id': user['live_code_id'],
            'img': open(get_img('cat1.jpg'), 'rb')
            }
        resp = await cli.post('/wx/user/img', data=data, headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        item = fs_user_img.find({'metadata.open_id': user['session_id']})
        assert len(list(item)) == 1

        item = db.live_code.find_one({'open_id': user['session_id']})
        assert isinstance(item['img'], dict)
        assert len(item['img']) == 1

    async def test_case_2(self, cli, user):
        data = MultiDict([
            ('live_code_id', user['live_code_id']),
            ('img',  open(get_img('cat1.jpg'), 'rb')),
            ('img',  open(get_img('cat2.jpg'), 'rb'))
        ])

        resp = await cli.post('/wx/user/img', data=data, headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        item = fs_user_img.find({'metadata.open_id': user['session_id']})
        assert len(list(item)) == 2

        item = db.live_code.find_one({'open_id': user['session_id']})
        assert isinstance(item['img'], dict)
        assert len(item['img']) == 2



