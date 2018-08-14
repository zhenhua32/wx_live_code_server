# API 接口文档

## /wx/login

微信登录的接口

```json
// post
{
    "code": "微信给的code"
}
// return
{
    "errcode": 0,
    "data": {
        "session_id": "其他请求必备, 放在headers['sesion_id']"
    }
}
// error: status=400
{
    "errcode": 1,
    "msg": ""
}
```

## /wx/user/live_code

用户创建管理 live_code

```json
// get 获取一个或所有的 live_code
/wx/user/live_code?id={}
// return
{
    "errcode": 0,
    "data": {
        "result": [{
            "id": "live_code 的唯一标识, _id 的 string 表示",
            "open_id": "用户的 open_id",
            "src": "二维码路径, 以 / 开头",
            "title": "标题",
            "date": "创建日期",
            "max_scan": "扫描阈值",
            "all_scan": "已扫描次数",
            "img": {
                "id": {
                    "id": "图片的唯一标识, _id 的 string 表示",
                    "date": "创建日期",
                    "scan": "已扫描次数",
                    "src": "图片的路径, 以 / 开头"
                }
            }
        }]
    }
}
```

```json
// put 创建一个新的 live_code
{
    "title": "活码标题",
    "max": "活码的扫描阈值"
}
// return
{
    "errcode": 0,
    "data": {
        "id": "新建的活码的 live_code_id"
    }
}
```

```json
// post 修改一个 live_code
{
    "id": "live_code 的 _id",
    "title": "新的标题",
    "max": "新的扫描阈值, 对应 live_code 的 max_scan"
}
// return
{
    "errcode": 0
}
```

```json
// delete 删除一个或多个 lilve_code
{
    "ids": ["live_code 的 _id"]
}
// return
{
    "errcode": 0
}
```


## /wx/user/img

用户为 live_code 添加图片

```json
// post 上传图片, multipart/form-data
{
    "live_code_id": "live_code 的 _id",
    "img": ["图片的二进制数据"]
}
// return
{
    "errcode": 0,
    "data": {
        "img": [{
            "id": "图片的 _id",
            "src": "图片的路径, 以 / 开头",
            "scan": "已扫描次数, 固定为0",
            "date": "创建日期"
        }]
    }
}
```

```json
// delete 删除图片
{
    "live_code_id": "live_code 的 _id",
    "ids": ["图片的 _id"]
}
// return
{
    "errcode": 0
}
```

## /to/{id}

live_code 跳转到用户上传的图片上

## /file/live_code/{filename}

live_code 图片

## /file/user_img/{filename}

用户上传的图片


