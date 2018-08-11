import datetime
import json
from aiohttp import web



def get_empty_user():
    return {
        'open_id': None,
        'session_key': None,
        'live_code_list': [],
        'join_at': datetime.datetime.now(),
        'last_visit': datetime.datetime.now()
    }


class Login(web.View):
    async def post(self):
        """用户登录注册"""
        users = self.request.app['db'].users

        code = self.request['body'].get('code', None)
        if not code:
            return web.json_response({
                'errcode': 1,
                'msg': '没有 code 参数'
            }, status=400)

        appid = self.request.app['config']['wx']['appid']
        secret = self.request.app['config']['wx']['secret']
        url = self.request.app['config']['wx']['authorization_code_url'].format(appid, secret, code)
        client_session = self.request.app['client_session']

        async with client_session.get(url) as resp:
            if resp.status != 200:
                return web.json_response({'errcode': 1, 'msg': '微信验证失败'}, status=400)
            
            body = json.loads(await resp.text())
            if 'errcode' in body:
                return web.json_response({'errcode': 1, 'msg': body}, status=400)
            
            return await self.login(body)

    async def login(self, body):
        users = self.request.app['db'].users

        open_id = body['openid']
        session_key = body['session_key']

        item = await users.find_one({'open_id': open_id})
        if item:
            # 更新用户的信息
            update = {
                '$set': {
                    'session_key': session_key,
                    'last_visit': datetime.datetime.now()
                }
            }
            await users.update_one({'open_id': open_id}, update)
        else:
            user = get_empty_user()
            user['open_id'] = open_id
            user['session_key'] = session_key
            await users.insert_one(user)
        
        return web.json_response({
            'errcode': 0,
            'data': {
                'session_id': open_id
            }
        })
        


