import datetime
import json
from aiohttp import web
from aiohttp.helpers import sentinel



def get_file_url(app, route_name, param:dict):
    url = app.router[route_name].url_for(**param)
    return str(url)

def get_file_urls(app, name, param:dict):
    # 一个假设, list 的长度是一样的
    urls = []
    value_len = [len(x) for x in param.values() if isinstance(x, list)]
    if value_len:
        max_len = value_len[0]
        assert max(value_len) == min(value_len)
    else:
        max_len = 1

    new_param = dict()
    for k, v in param.items():
        if isinstance(v, list):
            new_param[k] = v
        else:
            new_param[k] = [v]*max_len
    
    urls = []
    for i in range(max_len):
        temp = dict()
        for k, v in new_param.items():
            temp[k] = v[i]
        urls.append(get_file_url(app, name, temp))

    return urls

def get_str_date(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')


def default(obj):
    if isinstance(obj, datetime.datetime):
        return get_str_date(obj)


# 稍微改写了 web.json_response, 支持 datetime
def json_response(data=sentinel, *, text=None, body=None, status=200,
                  reason=None, headers=None, content_type='application/json'):
    if data is not sentinel:
        if text or body:
            raise ValueError(
                "only one of data, text, or body should be specified"
            )
        else:
            text = json.dumps(data, default=default)
    return web.Response(text=text, body=body, status=status, reason=reason,
                    headers=headers, content_type=content_type)


