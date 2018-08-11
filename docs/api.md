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
// get
// return
{
    "errcode": 0,
    "data": {
        "result": []
    }
}
```

```json
// post
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



## /wx/user/img

用户为 live_code 添加图片

## /to/{id}

live_code 跳转到用户上传的图片上

## /file/live_code/{filename}

live_code 图片

## /file/user_img/{filename}

用户上传的图片


