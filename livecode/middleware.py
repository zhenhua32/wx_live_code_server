from aiohttp import web
from aiohttp.web import middleware
from multidict import MultiDict

def is_need_verify(url, rule=None, skip=None):
    """
    写得有点简单, 只用 startswith 匹配
    测试 url 是否有效, 如果返回 True, 表明 url 需要验证
    :param url: 需要测试的 url, url 必须以 / 开头, 没有域名
    :param rule: 如果为 None 或 [] 就是全部都要满足, 否则满足其中一个规则就返回 True
    :param skip: 多个排除项, skip 优先于 rule
    :return:
    """
    if rule:
        if not isinstance(rule, list):
            rule = [rule]
    else:
        rule = []

    if skip:
        if not isinstance(skip, list):
            skip = [skip]
    else:
        skip = []

    # 满足任一排除项, 返回 False
    if any([url.startswith(x) for x in skip]):
        return False

    # 所有的规则中一个都不满足, 返回 False
    if rule and all([not url.startswith(x) for x in rule]):
        return False

    return True


@middleware
async def get_openid(request, handler):
    """
    添加 request['open_id']
    """
    url = str(request.rel_url)
    skip_urls = ['/wx/login']

    
    if is_need_verify(url, '/wx', skip_urls):
        open_id = request.headers.get('session_id', None)
        if not open_id:
            return web.json_response({
                'errcode': 1,
                'msg': '没有 session_id'
            })
        request['open_id'] = open_id
    
    resp = await handler(request)
    return resp


@middleware
async def parse_content(request, handler):
    """
    为 GET 和 POST 方法添加 request['body']
    """
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        if 'json' in request.content_type:
            body = await request.json()
            body = MultiDict(**body)
        else:
            body = await request.post()
        request['body'] = body
    elif request.method == 'GET':
        match_info = request.match_info
        query = request.query
        request['body'] = MultiDict(**match_info, **query)


    resp = await handler(request)
    return resp



