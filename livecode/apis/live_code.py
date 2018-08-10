import base64
import datetime
from io import BytesIO
from aiohttp import web
from bson import ObjectId
import qrcode
from ..tools.utils import get_file_url
from ..validate import s_UserLiveCode_post, s_LiveCodeRedirect_get


class LiveCodeRedirect(web.View):
    async def get(self):
        """活码跳转"""
        collection_live_code = self.request.app['db'].live_code

        item_id = self.request['body'].get('id', None)

        try:
            item_id = s_LiveCodeRedirect_get.validate(item_id)
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=404)

        item = await collection_live_code.find_one({'_id': item_id})
        if not item:
            return web.json_response({'errcode': 1, 'msg': 'id 不存在'}, status=404)
        
        max_scan = item.get('max_scan', 100)
        img = item.get('img', [])

        for img_id,img_count in img.items():
            if img_count < max_scan:
                # 找到可以跳转的图片
                img_url = get_file_url(self.request.app, 'user_img', param={'filename': img_id})
                update = {
                    '$inc': {
                        'all_scan': 1,
                        f'img.{img_id}': 1
                    }
                }
                await collection_live_code.update_one({'_id': item_id}, update)
                return web.HTTPFound(img_url)
        
        return web.json_response({'errcode': 1, 'msg': '没有可以跳转的图片'}, status=404)
        



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
            item['img'] = [get_file_url(self.request.app, 'user_img', param={'filename': x}) for x in item['img'].keys()]
            results.append(item)

        data = {'result': results}

        return web.json_response({'errcode': 0, 'data': data})

    async def post(self):
        """增加一个 live_code  """
        users = self.request.app['db'].users
        collection_live_code = self.request.app['db'].live_code
        open_id = self.request['open_id']

        title = self.request['body'].get('title', None)
        max_scan = self.request['body'].get('max', None)

        try:
            validated = s_UserLiveCode_post.validate({'title': title, 'max_scan': max_scan})
            max_scan = validated['max_scan']
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)
        
        # 先插入数据库, 在生成二维码
        one_live_code = {
            'open_id': open_id,
            'title': title,
            'date': datetime.datetime.now(),
            'src': None,
            'img_count': 0,
            'max_scan': max_scan,
            'all_scan': 0,
            'img': {}
        }

        result = await collection_live_code.insert_one(one_live_code)
        live_code_id = str(result.inserted_id)
        data = {
            'id': live_code_id
        }

        # 创建活码
        file_name = base64.urlsafe_b64encode(f'{open_id}_{live_code_id}.png'.encode('utf-8')).decode('utf-8')
        file_src = await self.create_qrcode(file_name, open_id, live_code_id)

        # 更新活码 ,更新用户的活码列表
        await collection_live_code.update_one({'_id': ObjectId(live_code_id)}, {'$set': {'src': file_src}})
        await users.update_one({'open_id': open_id}, {'$push': {'live_code_list': live_code_id}})

        return web.json_response({'errcode': 0, 'data': data})

    async def create_qrcode(self, file_name, open_id, live_code_id):
        """创建活码"""
        fs_live_code_img = self.request.app['fs_live_code_img']

        # 这里的 url 是一个会重定向的网址
        url = get_file_url(self.request.app, 'live_code_redirect', {'id': live_code_id})
        qr = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make()
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="png")

        file_id = await fs_live_code_img.upload_from_stream(
            file_name,
            buffered.getvalue(),
            chunk_size_bytes=16 * 1000 * 1000,
            metadata={'content_type': 'image/png', 'open_id': open_id}
        )
        file_id = str(file_id)
        file_src = get_file_url(self.request.app, 'live_code_img', {'filename': file_id})

        return file_src



