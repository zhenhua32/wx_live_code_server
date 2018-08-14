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
def user_delete():
    one = get_empty_user()
    one['open_id'] = 'test_live_code_delete'
    live_code_list = []

    one_lc = db.live_code.insert_one({'hello': 0, 'open_id': one['open_id']})
    live_code_list.append(str(one_lc.inserted_id))
    one_lc = db.live_code.insert_one({'hello': 1, 'open_id': one['open_id']})
    live_code_list.append(str(one_lc.inserted_id))

    one['live_code_list'] = live_code_list
    db.users.insert_one(one)
    yield {
        'session_id': one['open_id'],
        'live_code_ids': live_code_list
    }
    client.drop_database(db)


@pytest.fixture(scope='function')
def user_patch():
    one = get_empty_user()
    one['open_id'] = 'test_live_code_delete'
    live_code_list = []

    one_lc = db.live_code.insert_one({
        'hello': 0, 
        'open_id': one['open_id'],
        'title': 'hello',
        'max_scan': 100
    })
    live_code_list.append(str(one_lc.inserted_id))

    one['live_code_list'] = live_code_list
    db.users.insert_one(one)
    yield {
        'session_id': one['open_id'],
        'live_code_ids': live_code_list
    }
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
            str(img_id): {
                'scan': 0
            }
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
            str(img_id): {
                'scan': 100
            }
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
        # 测试 put UserLiveCode
        data = {'title': 'title 1', 'max': 100}
        resp = await cli.put('/wx/user/live_code', json=data, headers=user)
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
        # 测试 put UserLiveCode 的参数不正确的情况
        data = {}
        resp = await cli.put('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400
        
        data = {'title': 'hello'}
        resp = await cli.put('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400

        data = {'title': 'hello', 'max': 5}
        resp = await cli.put('/wx/user/live_code', json=data, headers=user)
        assert resp.status == 400

    async def test_case_5(self, cli, user_delete):
        # 测试删除单个 live_code
        data = {'ids': user_delete['live_code_ids'][:1]}
        headers = {'session_id': user_delete['session_id']}
        resp = await cli.delete('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        assert db.live_code.count_documents({}) == 1
        user = db.users.find_one({'open_id': user_delete['session_id']})
        assert len(user['live_code_list']) == 1
    
    async def test_case_6(self, cli, user_delete):
        # 测试删除多个 live_code
        data = {'ids': user_delete['live_code_ids']}
        headers = {'session_id': user_delete['session_id']}
        resp = await cli.delete('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        assert db.live_code.count_documents({}) == 0
        user = db.users.find_one({'open_id': user_delete['session_id']})
        assert len(user['live_code_list']) == 0

    async def test_case_7(self, cli, user_delete):
        # 测试删除 live_code 时的用户权限, 用户不拥有某个 live_code_id
        data = {'ids': user_delete['live_code_ids'] + [str(ObjectId())]}
        headers = {'session_id': user_delete['session_id']}
        resp = await cli.delete('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 401
        body = await resp.json()
        assert body['errcode'] == 1
        assert body['msg'] == '没有权限'

        data = {'ids': user_delete['live_code_ids'] + ['hello']}
        resp = await cli.delete('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 400

    async def test_case_8(self, cli, user_patch):
        # 测试更新 live_code
        data = {
            'id': user_patch['live_code_ids'][0],
            'title': 'new hello',
            'max': '80'
        }
        headers = {'session_id': user_patch['session_id']}
        resp = await cli.post('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert body['errcode'] == 0

        one_live_code = db.live_code.find_one({'_id': ObjectId(user_patch['live_code_ids'][0])})
        assert one_live_code['title'] == 'new hello'
        assert one_live_code['max_scan'] == 80
    
    async def test_case_9(self, cli, user_patch):
        # 测试更新 live_code 的一部分
        data = {
            'id': user_patch['live_code_ids'][0],
            'title': 'new hello',
            'max': '80'
        }
        headers = {'session_id': user_patch['session_id']}
        resp = await cli.post('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200

        data = {
            'id': user_patch['live_code_ids'][0],
            'title': 'new hello',
        }
        resp = await cli.post('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200

        data = {
            'id': user_patch['live_code_ids'][0],
            'max': '80'
        }
        resp = await cli.post('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 200

    async def test_case_10(self, cli, user_patch):
        # 测试更新 live_code 时的权限
        data = {
            'id': str(ObjectId()),
            'title': 'new title'
        }
        headers = {'session_id': user_patch['session_id']}
        resp = await cli.post('/wx/user/live_code', json=data, headers=headers)
        assert resp.status == 401


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
        # 测试图片跳转
        resp = await cli.get('/to/'+add_img['id'])
        assert resp.status == 200
        assert resp.headers.get('Content-Type', '') == 'image/png'

        item = db.live_code.find_one({'_id': ObjectId(add_img['id'])})
        assert item['all_scan'] == 1
        assert list(item['img'].values())[0]['scan'] == 1
    
    async def test_case_3(self, cli, add_img_max):
        # 测试图片跳转, 所有的图片的跳转次数都满了, 无法跳转
        resp = await cli.get('/to/'+add_img_max['id'])
        assert resp.status == 404
        body = await resp.json()
        assert body['msg'] == '没有可以跳转的图片'






