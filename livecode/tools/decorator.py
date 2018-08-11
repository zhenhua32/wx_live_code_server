from functools import wraps
from bson import ObjectId
from aiohttp import web


def check_live_code(func):
    """
    检查用户的 open_id 和 live_code_id 是否权限一致,
    必须在 body 中存在 live_code_id 
    """
    @wraps(func)
    async def wrapped(*args, **kwargs):
        func_self = args[0]

        open_id = func_self.request['open_id']
        live_code_id = func_self.request['body'].get('live_code_id', None)
        collection_live_code = func_self.request.app['db'].live_code

        item = await collection_live_code.find_one({'_id': ObjectId(live_code_id), 'open_id': open_id})
        if not item:
            return web.json_response({'errcode': 1, 'msg': '没有权限'}, status=401)

        return await func(*args, **kwargs)
    
    return wrapped


