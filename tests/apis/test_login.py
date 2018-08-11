import pytest
import qrcode
import json
from io import BytesIO
from aiohttp import web
from multidict import MultiDict
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from livecode.middleware import parse_content, get_openid
from livecode.apis.login import get_empty_user, Login
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

    app.router.add_view('/wx/login', Login)

    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture(scope='function')
def user():
    db.users.insert_one({'open_id': 'test_exist'})
    yield {}
    client.drop_database(db)


class TestLogin:
    async def test_case_1(self, cli):
        resp = await cli.post('/wx/login')
        assert resp.status == 400
    
    async def test_case_2(self, cli):
        resp = await cli.post('/wx/login', json={'code': '121'})
        body = await resp.json()
        assert resp.status == 400
        assert body['errcode'] == 1

    async def test_case_3(self, cli, user):
        resp = await Login(cli.server).login({
            'openid': 'test_login',
            'session_key': 'test_login'
        })
        assert resp.status == 200
        body = json.loads(resp.body)
        assert body['errcode'] == 0
        assert body['data']['session_id'] == 'test_login'

        assert db.users.count_documents({}) == 2
        assert db.users.find_one({'open_id': 'test_login'})
    
    async def test_case_4(self, cli, user):
        resp = await Login(cli.server).login({
            'openid': 'test_exist',
            'session_key': 'test_exist'
        })
        assert resp.status == 200
        body = json.loads(resp.body)
        assert body['errcode'] == 0
        assert body['data']['session_id'] == 'test_exist'

        assert db.users.count_documents({}) == 1






