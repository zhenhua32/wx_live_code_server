from aiohttp import web
from .route import routes


def main():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)

if __name__ == '__main__':
    main()
