import pytest
import qrcode
from io import BytesIO
from aiohttp import web
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from livecode.middleware import parse_content, get_openid
from livecode.apis.login import get_empty_user
from livecode.apis.live_code import LiveCodeRedirect, UserLiveCode
from livecode.db import init_motor, init_resource, init_gridfs_resource
from tests.help import config


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

    app.router.add_view('/wx/user/live_code', UserLiveCode)
    app.router.add_view(r'/to/{id}', LiveCodeRedirect, name='live_code_redirect')

    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture(scope='function')
def user():
    one = get_empty_user()
    one['open_id'] = 'test_live_code'
    db.users.insert_one(one)
    yield {'session_id': one['open_id']}
    client.drop_database(db)


@pytest.fixture(scope='function')
def add_img():
    buffered = BytesIO()
    img = qrcode.make('hello')
    img.save(buffered, format='png')

    img_id = fs_user_img.put(buffered, metadata={'content_type': 'image/png'})

    result = db.live_code.insert_one({
        'max_scan': 100,
        'all_scan': 0,
        'img': {
            str(img_id): 0
        }
    })

    live_code_id = str(result.inserted_id)
    yield {'id': live_code_id}
    client.drop_database(db)


@pytest.fixture(scope='function')
def add_img_max():
    buffered = BytesIO()
    img = qrcode.make('hello')
    img.save(buffered, format='png')

    img_id = fs_user_img.put(buffered, metadata={'content_type': 'image/png'})

    result = db.live_code.insert_one({
        'max_scan': 100,
        'all_scan': 0,
        'img': {
            str(img_id): 100
        }
    })

    live_code_id = str(result.inserted_id)
    yield {'id': live_code_id}
    client.drop_database(db)



class TestUserLiveCode:
    async def test_case_1(self, cli, user):
        # 测试 create_qrcode 函数
        file_src = await UserLiveCode(cli.server).create_qrcode(
            'fake.png',
            user['session_id'],
            'fake_live_code_id'
        )
        assert isinstance(file_src, str)

        assert fs_live_code_img.exists(ObjectId(file_src.split('/')[-1]))

        resp = await cli.get(file_src)
        assert resp.status == 200
        assert resp.headers.get('Content-Type', '') == 'image/png'
        
    async def test_case_2(self, cli, user):
        # 测试 get UserLiveCode
        resp = await cli.get('/wx/user/live_code', headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0
        assert isinstance(body['data']['result'], list)
        assert len(body['data']['result']) == 0

    async def test_case_3(self, cli, user):
        # 测试 post UserLiveCode
        data = {'title': 'title 1', 'max': 100}
        resp = await cli.post('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        live_code_id = body['data']['id']
        item = db.live_code.find_one({'_id': ObjectId(live_code_id)})
        assert item

        item_user = db.users.find_one({'open_id': user['session_id']})
        assert len(item_user['live_code_list']) == 1

        resp = await cli.get('/wx/user/live_code', headers=user)
        assert resp.status == 200
        body = await resp.json()
        assert len(body['data']['result']) == 1

    async def test_case_4(self, cli, user):
        # 测试 post UserLiveCode 的参数不正确的情况
        data = {}
        resp = await cli.post('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400
        
        data = {'title': 'hello'}
        resp = await cli.post('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400

        data = {'title': 'hello', 'max': 5}
        resp = await cli.post('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400


class TestLiveCodeRedirect:
    async def test_case_1(self, cli):
        # 测试错误的 id
        resp = await cli.get('/to/')
        assert resp.status == 404

        resp = await cli.get('/to/id')
        assert resp.status == 404

        resp = await cli.get('/to/5b6d27c83417f3bf00dc3acd')
        assert resp.status == 404
    
    async def test_case_2(self, cli, add_img):
        resp = await cli.get('/to/'+add_img['id'])
        assert resp.status == 200
        assert resp.headers.get('Content-Type', '') == 'image/png'

        item = db.live_code.find_one({'_id': ObjectId(add_img['id'])})
        assert item['all_scan'] == 1
        assert list(item['img'].values())[0] == 1
    
    async def test_case_3(self, cli, add_img_max):
        resp = await cli.get('/to/'+add_img_max['id'])
        assert resp.status == 404
        body = await resp.json()
        assert body['msg'] == '没有可以跳转的图片'






