import datetime
from aiohttp import web
from bson import ObjectId
from ..validate import s_UserImg_post, s_UserImg_delete
from ..tools.decorator import check_live_code
from ..tools.utils import get_file_url, get_str_date


class UserImg(web.View):
    @check_live_code
    async def post(self):
        """为活码上传图片"""
        open_id = self.request['open_id']
        fs_user_img = self.request.app['fs_user_img']
        collection_live_code = self.request.app['db'].live_code

        img = self.request['body'].getall('img', [])
        live_code_id = self.request['body'].get('live_code_id', None)

        try:
            s_UserImg_post.validate({
                'live_code_id': live_code_id,
                'img': img
            })
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)

        update_img = {}
        img_data = []
        for item in img:
            file_name = item.filename
            file_content = item.file.read()
            content_type = item.content_type
            
            file_id = await fs_user_img.upload_from_stream(
                file_name,
                file_content,
                chunk_size_bytes=16 * 1000 * 1000,
                metadata={'content_type': content_type, 'open_id': open_id}
            )
            file_id = str(file_id)
            now = datetime.datetime.now()
            update_img[f'img.{file_id}'] = {
                'scan': 0,
                'date': now
            }
            img_data.append({
                'src': get_file_url(self.request.app, 'user_img', param={'filename': file_id}),
                'scan': 0,
                'date': get_str_date(now)
            })
        
        await collection_live_code.update_one({'_id': ObjectId(live_code_id)}, {'$set': update_img})

        return web.json_response({'errcode': 0, 'data': {'img': img_data}})

    @check_live_code
    async def delete(self):
        """删除活码下的图片"""
        open_id = self.request['open_id']
        fs_user_img = self.request.app['fs_user_img']
        collection_live_code = self.request.app['db'].live_code

        if isinstance(self.request['body'], dict):
            img_ids = self.request['body'].get('ids', [])
        else:
            img_ids = self.request['body'].getall('ids', [])

        live_code_id = self.request['body'].get('live_code_id', None)

        try:
            s_UserImg_delete.validate({
                'img_ids': img_ids,
                'live_code_id': live_code_id
            })
        except Exception as e:
            return web.json_response({'errcode': 1, 'msg': str(e)}, status=400)

        update_img = {}
        for x in img_ids:
            update_img[f'img.{x}'] = None
        
        await collection_live_code.update_one({'_id': ObjectId(live_code_id)}, {'$unset': update_img})
        for x in img_ids:
            await fs_user_img.delete(ObjectId(x))
        
        return web.json_response({'errcode': 0})
