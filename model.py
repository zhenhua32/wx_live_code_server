import datetime

"""
数据模型, 使用 mongodb
"""

# 用户模型
user_template = {
    '_id': '',                      
    'open_id': '',                      
    'session_id': '',                      
    'live_code_list': [],       # 活码列表, 保存的是 id               
}

# 活码模型
live_code_template = {
    '_id': '',                        #       
    'title': '',                      # 标题        
    'date': datetime.datetime.now(),  # 创建日期                            
    'src': '',                        # 活码的地址, https 地址      
    'img_count': 0,                   #            
    'max_scan': 100,                  # 扫描的阈值, 每当达到阈值的时候会换下一张二维码            
    'all_scan': 0,                    # 总的扫描次数
    'img': [],                        # 二维码, 保存的是 id                           

}

# 活码的二维码存储, 使用 gridfs
live_code_img_template = {
    '_id': '',
    'filename': '',
    'md5': '',
    'chunkSize': '',
    'metadata': {
        'open_id': '',          # 连接到 user
        'live_code_id': '',     # 连接到 live_code   
    }

}

# 用户上传的二维码, 使用 gridfs
user_img_template = {
    '_id': '',
    'filename': '',
    'md5': '',
    'chunkSize': '',
    'metadata': {
        'open_id': '',         # 连接到 user
        'live_code_id': '',    # 连接到 live_code
    }
}

