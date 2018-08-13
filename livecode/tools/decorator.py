from functools import wraps
from bson import ObjectId
from aiohttp import web
from schema import Schema
from ..validate import obejct_id_schema


class CheckLiveCode:
    def __init__(self, live_code_filed='live_code_id'):
        self.live_code_filed = live_code_filed
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_self = args[0]

            open_id = func_self.request['open_id']
            live_code_ids = func_self.request['body'].get(self.live_code_filed, None)
            collection_live_code = func_self.request.app['db'].live_code

            if not live_code_ids:
                return web.json_response({'errcode': 1, 'msg': '没有 live_code_id'}, status =400)

            if not isinstance(live_code_ids, list):
                live_code_ids = [live_code_ids]

            try:
                Schema([obejct_id_schema]).validate(live_code_ids)
            except Exception as e:
                return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)
            
            for x in live_code_ids:
                item = await collection_live_code.find_one({'_id': ObjectId(x), 'open_id': open_id})
                if not item:
                    return web.json_response({'errcode': 1, 'msg': '没有权限'}, status=401)
            
            return await func(*args, **kwargs)

        return wrapper

