

def get_file_url(app, route_name, param:dict):
    url = app.router[route_name].url_for(**param)
    return str(url)

