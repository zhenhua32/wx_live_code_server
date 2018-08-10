import json
import os
from aiohttp import web
from .route import routes
from .middleware import parse_content, get_openid
from .db import init_motor, init_resource, init_gridfs_resource


dir_path = os.path.dirname(__file__)
config_path = os.path.join(dir_path, 'config.json')


def main(config_path=config_path):
    app = web.Application(middlewares=[parse_content, get_openid])
    app.add_routes(routes)

    config = json.load(open(config_path, 'r', encoding='utf-8'), encoding='utf-8')
    app['config'] = config

    app.on_startup.append(init_motor)
    app.on_startup.append(init_gridfs_resource)
    app.cleanup_ctx.append(init_resource)



    web.run_app(app)

if __name__ == '__main__':
    main()
