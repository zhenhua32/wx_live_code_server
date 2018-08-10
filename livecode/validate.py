from schema import Schema, And, Or, Use, Optional
from bson import ObjectId

"""
验证规则的集合
注意, 某些规则有转换类型的效果, 那些使用 Use 的规则
"""

s_UserLiveCode_post = Schema({
    'title': And(str, len, error='无效的标题'),
    'max_scan': And(Use(int), lambda x: 10 < x < 10000, error='阈值不符合范围')
})


s_LiveCodeRedirect_get = Schema(And(str, len, Use(ObjectId)), error='无效的id')

