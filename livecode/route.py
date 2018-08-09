from aiohttp import web
from .apis import hello
from .apis import login

routes_list = {
    '/': hello.Hello,
    '/login': login.Login
}

routes = []
for k, v in routes_list.items():
    routes.append(web.view(k, v))
