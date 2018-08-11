from aiohttp import web
from .apis import hello
from .apis import login
from .apis import live_code
from .apis import user_img

routes_list = {
    '/': hello.Hello,
    '/wx/login': login.Login,
    '/wx/user/live_code': live_code.UserLiveCode,
    '/wx/user/img': user_img.UserImg
}

routes = []
for k, v in routes_list.items():
    routes.append(web.view(k, v))

routes.append(web.view('/to/{id}', live_code.LiveCodeRedirect, name='live_code_redirect'))

