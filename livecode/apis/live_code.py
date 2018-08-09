from aiohttp import web
from bson import ObjectId
import qrcode
from ..lib.utils import get_file_url


class LiveCode(web.View):
    """
    我是希望将 live_code 的生态都建立在这里
    """
    async def get(self):
        users = self.request.app['db'].users
        open_id = self.request['open_id']

        user = await users.find_one({'open_id': open_id})

        



class UserLiveCode(web.View):
    """
    用户相关的 live_code 操作
    """
    async def get(self):
        """获取用户的所有 live_code"""
        users = self.request.app['db'].users
        collection_live_code = self.request.app['db'].live_code
        open_id = self.request['open_id']

        user = await users.find_one({'open_id': open_id})

        live_code_ids = [ObjectId(x) for x in user['live_code_list']]
        items = collection_live_code.find({'_id': {'$in': live_code_ids}}, {'_id': 0})

        results = []
        async for item in items:
            item['date'] = item['date'].strftime('%Y-%m-%d %H:%M:%S')
            item['img'] = [str(self.request.app.router['user_img'].url_for(filename=x)) for x in item['img']]
            item['img'] = [get_file_url(self.request.app, 'user_img', param={'filename': x}) for x in item['img']]
            results.append(item)


        

        return web.json_response({
            'errcode': 0,
            'data': data
        })




