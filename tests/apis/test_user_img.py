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


@pytest.fixture(scope='function')
def user_error():
    one = get_empty_user()
    one['open_id'] = 'test_user_img'
    db.users.insert_one(one)

    result = db.live_code.insert_one({
        'open_id': 'test_user_img_different',
        'img': {}
    })
    live_code_id = str(result.inserted_id)
    yield {'session_id': one['open_id'], 'live_code_id': live_code_id}
    client.drop_database(db)


@pytest.fixture(scope='function')
def user_delete():
    one = get_empty_user()
    one['open_id'] = 'test_user_img'
    db.users.insert_one(one)

    img_ids = {}
    one_id = fs_user_img.put(open(get_img('cat1.jpg'), 'rb'))
    img_ids[str(one_id)] = 0
    one_id = fs_user_img.put(open(get_img('cat2.jpg'), 'rb'))
    img_ids[str(one_id)] = 0

    result = db.live_code.insert_one({
        'open_id': 'test_user_img',
        'img': img_ids
    })
    live_code_id = str(result.inserted_id)
    yield {
        'session_id': one['open_id'], 
        'live_code_id': live_code_id,
        'img_ids': img_ids
    }
    client.drop_database(db)


class TestUserImg:
    async def test_case_1(self, cli, user):
        # 测试上传单张图片
        data = {
            'live_code_id': user['live_code_id'],
            'img': open(get_img('cat1.jpg'), 'rb')
            }
        resp = await cli.post('/wx/user/img', data=data, headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0
        assert len(body['data']['src']) == 1

        item = fs_user_img.find({'metadata.open_id': user['session_id']})
        assert len(list(item)) == 1

        item = db.live_code.find_one({'open_id': user['session_id']})
        assert isinstance(item['img'], dict)
        assert len(item['img']) == 1

    async def test_case_2(self, cli, user):
        # 测试上传多张图片
        data = MultiDict([
            ('live_code_id', user['live_code_id']),
            ('img',  open(get_img('cat1.jpg'), 'rb')),
            ('img',  open(get_img('cat2.jpg'), 'rb'))
        ])

        resp = await cli.post('/wx/user/img', data=data, headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0
        assert len(body['data']['src']) == 2

        item = fs_user_img.find({'metadata.open_id': user['session_id']})
        assert len(list(item)) == 2

        item = db.live_code.find_one({'open_id': user['session_id']})
        assert isinstance(item['img'], dict)
        assert len(item['img']) == 2

    async def test_case_3(self, cli, user_error):
        # 测试用户权限, open_id 和 live_code 中的 open_id 不一致
        data = {
            'live_code_id': user_error['live_code_id'],
            'img': open(get_img('cat1.jpg'), 'rb')
            }
        resp = await cli.post('/wx/user/img', data=data, headers=user_error)
        assert resp.status == 401

    async def test_case_4(self, cli, user_delete):
        # 测试删除单张图片, 使用普通 post
        data = {
            'live_code_id': user_delete['live_code_id'],
            'ids': list(user_delete['img_ids'].keys())
        }
        headers = {
            'session_id': user_delete['session_id']
        }
        resp = await cli.delete('/wx/user/img', data=data, headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        item = db.live_code.find_one({'_id': ObjectId(user_delete['live_code_id'])})
        assert len(item['img']) == 0

        for x in user_delete['img_ids'].keys():
            assert fs_user_img.exists(ObjectId(x)) is False

    async def test_case_5(self, cli, user_delete):
        # 测试删除单张图片, 使用普通 json
        data = {
            'live_code_id': user_delete['live_code_id'],
            'ids': list(user_delete['img_ids'].keys())
        }
        headers = {
            'session_id': user_delete['session_id']
        }
        resp = await cli.delete('/wx/user/img', json=data, headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        item = db.live_code.find_one({'_id': ObjectId(user_delete['live_code_id'])})
        assert len(item['img']) == 0

        for x in user_delete['img_ids'].keys():
            assert fs_user_img.exists(ObjectId(x)) is False


