from aiohttp import web
from .apis import hello

routes_list = {
    '/': hello.Hello
}

routes = []
for k, v in routes_list.items():
    routes.append(web.view(k, v))
