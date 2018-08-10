from aiohttp import web
from bson import ObjectId
from ..lib.utils import get_file_url


class UserImg(web.View):
    async def post(self):
        open_id = self.request['open_id']
        fs_user_img = self.request.app['fs_user_img']
        img = self.request['body'].getall('img', [])

        if not img:
            return web.json_response({'errcode': 0, 'msg': '没有图片'}, status=400)

        for item in img:
            file_name = item.filename
            file_content = item.file.read()
            content_type = item.content_type if item.content_type else ''

            # 判断文件类型, 只支持图片
            if not content_type.startswith('image/'):
                return web.json_response({
                    'errcode': 1,
                    'msg': '图片类型不正确'
                }, status=400)
            
            file_id = await fs_user_img.upload_from_stream(
                file_name,
                file_content,
                chunk_size_bytes=16 * 1000 * 1000,
                metadata={'content_type': content_type, 'open_id': open_id}
            )
            file_id = str(file_id)


