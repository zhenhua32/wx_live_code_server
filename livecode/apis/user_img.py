from aiohttp import web
from bson import ObjectId

from ..lib.utils import get_file_url
from ..validate import *


class UserImg(web.View):
    async def post(self):
        open_id = self.request['open_id']
        img = self.request['body'].getall('img', [])

        if not img:
            return web.json_response({'errcode': 0}, )


