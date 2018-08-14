import base64
import datetime
from io import BytesIO
from aiohttp import web
from bson import ObjectId
import qrcode
from ..tools.utils import get_file_url, get_str_date, json_response
from ..validate import s_LiveCodeRedirect_get, s_UserLiveCode_post, s_UserLiveCode_delete
from ..validate import s_UserLiveCode_patch
from ..tools.decorator import CheckLiveCode


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

        for img_id, v in img.items():
            if v['scan'] < max_scan:
                # 找到可以跳转的图片
                img_url = get_file_url(self.request.app, 'user_img', param={'filename': img_id})
                update = {'$inc': {'all_scan': 1, f'img.{img_id}.scan': 1}}
                await collection_live_code.update_one({'_id': item_id}, update)
                return web.HTTPFound(img_url)

        return web.json_response({'errcode': 1, 'msg': '没有可以跳转的图片'}, status=404)


class UserLiveCode(web.View):
    """
    用户相关的 live_code 操作
    """

    async def get(self):
        """获取单个或所有 live_code """
        users = self.request.app['db'].users
        collection_live_code = self.request.app['db'].live_code
        open_id = self.request['open_id']

        live_code_id = self.request['body'].get('id', None)

        if live_code_id:
            # 获取单个的 live_code
            item = await collection_live_code.find_one({'_id': ObjectId(live_code_id), 'open_id': open_id})
            if not item:
                return web.json_response({'errcode': 0, 'msg': 'live_code 不存在或没有权限'}, status=400)
            items = [item]
        else:
            # 获取用户的所有 live_code
            user = await users.find_one({'open_id': open_id})

            live_code_ids = [ObjectId(x) for x in user['live_code_list']]
            aitems = collection_live_code.find({'_id': {'$in': live_code_ids}})
            items = []
            async for item in aitems:
                items.append(item)

        # 返回的结果是数组, 不管获取单个还是多个 live_code
        results = []
        for item in items:
            item['id'] = str(item['_id'])
            del item['_id']
            for k, v in item['img'].items():
                v['id'] = k
                v['src'] = get_file_url(self.request.app, 'user_img', param={'filename': k})
            results.append(item)

        data = {'result': results}

        return json_response({'errcode': 0, 'data': data})

    async def put(self):
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
            'max_scan': max_scan,
            'all_scan': 0,
            'img': {}
        }

        result = await collection_live_code.insert_one(one_live_code)
        live_code_id = str(result.inserted_id)
        data = {'id': live_code_id}

        # 创建活码
        file_name = base64.urlsafe_b64encode(f'{open_id}_{live_code_id}'.encode('utf-8')).decode('utf-8') + '.png'
        file_src = await self.create_qrcode(file_name, open_id, live_code_id)

        # 更新活码 ,更新用户的活码列表
        await collection_live_code.update_one({'_id': ObjectId(live_code_id)}, {'$set': {'src': file_src}})
        await users.update_one({'open_id': open_id}, {'$push': {'live_code_list': live_code_id}})

        return web.json_response({'errcode': 0, 'data': data})

    @CheckLiveCode(live_code_filed='ids')
    async def delete(self):
        """删除单个或多个 live_code """
        users = self.request.app['db'].users
        collection_live_code = self.request.app['db'].live_code
        open_id = self.request['open_id']

        if isinstance(self.request['body'], dict):
            live_code_ids = self.request['body'].get('ids', [])
        else:
            live_code_ids = self.request['body'].getall('ids', [])

        try:
            s_UserLiveCode_delete.validate({'live_code_ids': live_code_ids})
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)

        update_user = {'$pull': {'live_code_list': {'$in': live_code_ids.copy()}}}

        live_code_ids = [ObjectId(x) for x in live_code_ids]
        await users.update_one({'open_id': open_id}, update_user)
        await collection_live_code.delete_many({'_id': {'$in': live_code_ids}, 'open_id': open_id})

        return web.json_response({'errcode': 0})

    @CheckLiveCode(live_code_filed='id')
    async def post(self):
        """
        更新单个 live_code, 不包括 img 部分
        又白写了, 小程序不支持 patch
        """
        users = self.request.app['db'].users
        collection_live_code = self.request.app['db'].live_code
        open_id = self.request['open_id']

        live_code_id = self.request['body'].get('id', None)

        # 更新 max_scan 的时候不做其他处理, 例如 img 的更新
        update_info = {
            'title': self.request['body'].get('title', None),
            'max_scan': self.request['body'].get('max', None)
        }
        update_info = {k: v for k, v in update_info.items() if v}

        try:
            for k, v in update_info.items():
                # 有类型转换
                new_v = s_UserLiveCode_patch[k].validate(v)
                update_info[k] = new_v
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)

        await collection_live_code.update_one({
            '_id': ObjectId(live_code_id),
            'open_id': open_id
        }, {'$set': update_info})

        return web.json_response({'errcode': 0})

    async def create_qrcode(self, file_name, open_id, live_code_id):
        """创建活码"""
        fs_live_code_img = self.request.app['fs_live_code_img']

        # 这里的 url 是一个会重定向的网址
        url = get_file_url(self.request.app, 'live_code_redirect', {'id': live_code_id})
        url = self.request.app['config']['host'] + url
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
            metadata={
                'content_type': 'image/png',
                'open_id': open_id
            })
        file_id = str(file_id)
        file_src = get_file_url(self.request.app, 'live_code_img', {'filename': file_id})

        return file_src
