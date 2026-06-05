"""
Koukoutu ComfyUI Nodes — 公共配置
所有节点共享的 API 地址、错误码、重试策略等常量集中管理于此
"""

# ====================== API 端点 ======================

# 同步 API（用于抠图等即时返回的接口）
SYNC_API_URL = "https://sync.koukoutu.com/v1/create"

# 异步 API（用于印花裁切、扩图、去水印等需要轮询的接口）
ASYNC_CREATE_URL = "https://async.koukoutu.com/v1/create"
ASYNC_QUERY_URL  = "https://async.koukoutu.com/v1/query"

# ====================== 认证方式 ======================

# 同步 API 使用 Bearer Token
SYNC_AUTH_HEADER = "Authorization"
SYNC_AUTH_PREFIX = "Bearer "

# 异步 API 使用 X-API-Key
ASYNC_AUTH_HEADER = "X-API-Key"

# ====================== 重试策略 ======================

# 服务器类错误，可自动重试
RETRY_STATUS_CODES = [500, 502, 503, 504]

# 最大重试次数
MAX_RETRY_COUNT = 5

# 异步轮询间隔（秒）
DEFAULT_POLL_INTERVAL = 1

# 异步任务最大等待时间（秒）
DEFAULT_MAX_WAIT = 300

# ====================== 请求超时 ======================

# 创建任务请求超时（秒）
CREATE_REQUEST_TIMEOUT = 120

# 轮询查询请求超时（秒）
QUERY_REQUEST_TIMEOUT = 30

# 下载结果图像超时（秒）
DOWNLOAD_REQUEST_TIMEOUT = 60

# ====================== 错误码映射 ======================

CODE_DICT = {
    200: "成功",
    401: "无效的 API Key, 请检查您的 Key 是否正确。查看KEY地址: https://www.koukoutu.com/user/dev",
    403: "API密钥无效或额度不足",
    404: "未找到",
    406: "文件大小超过15M",
    407: "图片分辨率小于70",
    409: "积分不足",
    413: "文件太大",
    415: "不支持的文件格式",
    422: "参数错误",
    429: "请求过于频繁",
    500: "服务器内部错误",
    502: "服务暂时不可用",
    503: "服务暂时不可用",
}
