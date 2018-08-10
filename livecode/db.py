from motor import motor_asyncio
import motor.aiohttp
import aiohttp
from bson import ObjectId


async def init_motor(app):
    host = '127.0.0.1'
    port = 27017
    client = motor_asyncio.AsyncIOMotorClient(host, port)
    db = client.live_code

    fs_live_code_img = motor_asyncio.AsyncIOMotorGridFSBucket(db, 'live_code_img')
    fs_user_img = motor_asyncio.AsyncIOMotorGridFSBucket(db, 'user_img')

    app['db'] = db
    app['fs_live_code_img'] = fs_live_code_img
    app['fs_user_img'] = fs_user_img


async def init_resource(app):
    app['client_session'] = aiohttp.ClientSession()
    yield
    await app['client_session'].close()

async def init_gridfs_resource(app):
    host = '127.0.0.1'
    port = 27017
    client = motor_asyncio.AsyncIOMotorClient(host, port).live_code


    def get_gridfile_by_id(bucket, filename, request):
        return bucket.open_download_stream(file_id=ObjectId(filename))

    def set_extra_headers(response, gridout):
        response.headers['Content-Type'] = gridout.metadata['content_type']

    def create_handler(pattern, collection, by='id', pattern_name=None):
        if by == 'id':
            handler = motor.aiohttp.AIOHTTPGridFS(client, root_collection=collection,
                                                  get_gridfs_file=get_gridfile_by_id,
                                                  set_extra_headers=set_extra_headers)

        elif by == 'name':
            handler = motor.aiohttp.AIOHTTPGridFS(client, root_collection=collection,
                                                  set_extra_headers=set_extra_headers)
        else:
            return

        # 注意 pattern 里一定要有 filename
        resource = app.router.add_resource(pattern, name=pattern_name)
        resource.add_route('GET', handler)
        resource.add_route('HEAD', handler)

    create_handler('/file/live_code/{filename}', 'live_code_img', by='id', pattern_name='live_code_img')
    create_handler('/file/user_img/{filename}', 'user_img', by='id', pattern_name='user_img')




