import io
import time
import requests
from PIL import Image
import comfy.utils

from ..config import (
        ASYNC_CREATE_URL,
        ASYNC_QUERY_URL,
        ASYNC_AUTH_HEADER,
        RETRY_STATUS_CODES,
        MAX_RETRY_COUNT,
        DEFAULT_POLL_INTERVAL,
        DEFAULT_MAX_WAIT,
        CREATE_REQUEST_TIMEOUT,
        QUERY_REQUEST_TIMEOUT,
        DOWNLOAD_REQUEST_TIMEOUT,
    )
from ..utils import (
        tensor_to_pil, 
        pil_to_tensor, 
        save_temp_image, 
        cleanup_temp_file,
        validate_api_key,
        code_dict
    )


class KoukoutuImageExtractV2:
    """
    Koukoutu 中阶印花提取节点
    使用抠抠图异步 API（image-extract-v2）从图像中提取指定类型的印花/图案，效果优于标准版
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "请输入您的 Koukoutu API Key"
                }),
                "extract_type": ("STRING", {
                    "default": "服装",
                    "multiline": False,
                    "placeholder": "提取类型，例如：服装、鞋包、配饰等"
                }),
            },
            "optional": {
                "resolution": (["1k", "4k"], {
                    "default": "1k",
                    "tooltip": "输出分辨率，4k 更清晰但耗时更长",
                }),
                "size": ([
                    "0:0",   "1:1",  "1:2",  "2:1",  "2:3",
                    "3:2",   "3:4",  "3:5",  "3:7",  "4:3",
                    "5:3",   "6:7",  "7:3",  "7:6",  "9:16",
                    "16:9",  "26:38","27:50","50:27",
                ], {
                    "default": "0:0",
                    "tooltip": "输出比例，0:0 表示按原图尺寸",
                }),
                "skip_error": ("BOOLEAN", {
                    "default": True,
                    "label_on": "跳过错误（返回原图 + 错误信息）",
                    "label_off": "抛出错误（中断流程）",
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("image", "message",)
    FUNCTION = "image_extract_v2"
    CATEGORY = "image/koukoutu"
    DESCRIPTION = "使用 Koukoutu API 中阶模型提取图像中的印花/图案（异步）"
    
    def image_extract_v2(self, image, api_key, extract_type,
                         resolution="1k", size="0:0",
                         skip_error=True, error_num=0):
        """
        中阶印花提取：
        1. 将图像保存为临时文件，以 image_file 方式上传
        2. 提交异步任务，获取 task_id
        3. 轮询查询结果：
           - state=1 成功：返回结果图像 + "成功"
           - state=2 错误：若 skip_error=True 返回原图 + 错误信息，否则抛出异常
        """
        try:
            # Validate API key
            validated_api_key = validate_api_key(api_key)
            
            headers = {
                ASYNC_AUTH_HEADER: validated_api_key
            }

            model_key = "image-extract-v2"

            # Convert ComfyUI image tensor to PIL Image and save as temp file
            pil_image = tensor_to_pil(image)
            temp_path = save_temp_image(pil_image, 'PNG')

            try:
                # ---- Step 1: 创建异步任务（image_file 方式）----
                data = {
                    'model_key': model_key,
                    'extract_type': extract_type,
                    'resolution': resolution,
                    'size': size,
                }
                files = {
                    'image_file': ('image.png', open(temp_path, 'rb'), 'image/png')
                }
                response = requests.post(
                    ASYNC_CREATE_URL,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=CREATE_REQUEST_TIMEOUT
                )

                # 解析创建任务响应
                json_response = response.json()
                code = json_response.get('code', 0)
                if code != 200:
                    if code in RETRY_STATUS_CODES and error_num <= MAX_RETRY_COUNT:
                        return self.image_extract_v2(
                            image, api_key, extract_type, resolution,
                            size, skip_error, error_num + 1
                        )
                    else:
                        raise Exception(code_dict.get(code, f"创建任务失败: {json_response.get('message', '未知错误')}"))

                task_id = json_response.get('data', {}).get('task_id')
                if not task_id:
                    raise Exception(f"API 返回中未找到 task_id: {json_response}")

                # ---- Step 2: 轮询查询结果 ----
                max_wait = DEFAULT_MAX_WAIT
                poll_interval = DEFAULT_POLL_INTERVAL
                elapsed = 0
                pbar = comfy.utils.ProgressBar(100)

                while elapsed < max_wait:
                    query_response = requests.post(
                        ASYNC_QUERY_URL,
                        headers=headers,
                        data={
                            'task_id': str(task_id),
                            'response': 'url',
                            'model_key': model_key,
                        },
                        timeout=QUERY_REQUEST_TIMEOUT
                    )
                    query_json = query_response.json()
                    query_code = query_json.get('code', 0)

                    if query_code != 200:
                        if query_code in RETRY_STATUS_CODES and error_num <= MAX_RETRY_COUNT:
                            return self.image_extract_v2(
                                image, api_key, extract_type, resolution,
                                size, skip_error, error_num + 1
                            )
                        else:
                            raise Exception(code_dict.get(query_code, f"查询任务失败: {query_json.get('message', '未知错误')}"))

                    query_data = query_json.get('data', {})
                    state = query_data.get('state', 0)
                    result_file = query_data.get('result_file')
                    msg = query_data.get('message', '')

                    if state == 1 and result_file:
                        # ---- Step 3: 下载结果图像 ----
                        result_response = requests.get(result_file, timeout=DOWNLOAD_REQUEST_TIMEOUT)
                        if result_response.status_code != 200:
                            raise Exception(f"下载结果图像失败，HTTP {result_response.status_code}")
                        result_image = Image.open(io.BytesIO(result_response.content))
                        result_tensor = pil_to_tensor(result_image)
                        return (result_tensor, "成功",)

                    if state == 2:
                        error_msg = msg if msg else "任务处理失败，未知错误"
                        print(f"[Koukoutu] 任务 {task_id} 出错: {error_msg}")
                        if skip_error:
                            return (image, error_msg,)
                        else:
                            raise Exception(f"中阶印花提取失败: {error_msg}")

                    # state == 0: 任务仍在运行，等待后重试
                    progress = query_data.get('progress', '0')
                    try:
                        progress_val = int(float(progress))
                    except (ValueError, TypeError):
                        progress_val = 0
                    pbar.update_absolute(progress_val, 100)
                    print(f"[Koukoutu] 任务 {task_id} 运行中… 进度: {progress}%")
                    time.sleep(poll_interval)
                    elapsed += poll_interval

                raise Exception(f"任务超时（等待超过 {max_wait} 秒），task_id: {task_id}")

            finally:
                cleanup_temp_file(temp_path)
                
        except requests.RequestException as e:
            if error_num <= MAX_RETRY_COUNT:
                return self.image_extract_v2(
                    image, api_key, extract_type, resolution,
                    size, skip_error, error_num + 1
                )
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            raise Exception(f"中阶印花提取失败: {str(e)}")
    
    @classmethod
    def IS_CHANGED(cls, image, api_key, extract_type,
                   resolution="1k", size="0:0", skip_error=True):
        """
        This method helps ComfyUI determine when to re-execute the node
        Returns a hash of the input parameters to enable intelligent caching
        """
        import hashlib
        
        if image is not None:
            image_hash = hashlib.md5(image.cpu().numpy().tobytes()).hexdigest()[:16]
        else:
            image_hash = "no_image"
        
        params_str = (
            f"{image_hash}_{api_key[:8] if api_key else 'no_key'}"
            f"_{extract_type}_{resolution}_{size}_{skip_error}"
        )
        return hashlib.md5(params_str.encode()).hexdigest()[:16]
