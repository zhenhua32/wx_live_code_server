from aiohttp import web


class Hello(web.View):
    async def get(self):
        return web.json_response({'hello': 'world'})


