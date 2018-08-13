from schema import Schema, And, Or, Use, Optional
from bson import ObjectId

"""
验证规则的集合
注意, 某些规则有转换类型的效果, 那些使用 Use 的规则
"""

obejct_id_schema = And(str, len, Use(ObjectId), error='无效的 id' )
title_schema = And(str, len, error='无效的标题')
max_scan_schema = And(Use(int), lambda x: 10 < x < 10000, error='阈值不符合范围')

s_UserLiveCode_post = Schema({
    'title': title_schema,
    'max_scan': max_scan_schema
})

s_UserLiveCode_delete = Schema({
    'live_code_ids': [obejct_id_schema]
})

s_UserLiveCode_patch = {
    'title': Schema(title_schema),
    'max_scan': Schema(max_scan_schema)
}

s_LiveCodeRedirect_get = Schema(And(str, len, Use(ObjectId)), error='无效的id')

s_UserImg_post = Schema({
    'live_code_id': obejct_id_schema,
    'img': And(len, [lambda x: x.content_type.startswith('image/')], error='无效的 img')
})

s_UserImg_delete = Schema({
    'live_code_id': obejct_id_schema,
    'img_ids': [obejct_id_schema]
})



