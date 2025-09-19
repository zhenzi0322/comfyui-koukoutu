import io
import requests
from PIL import Image

from ..utils import (
        tensor_to_pil, 
        pil_to_tensor, 
        save_temp_image, 
        cleanup_temp_file,
        validate_api_key
    )

code_dict = {
    401: "无效的 API Key, 请检查您的 Key 是否正确。查看KEY地址: https://www.koukoutu.com/user/dev",
    200: "成功",
    403: "API密钥无效或额度不足",
    404: "未找到",
    413: "文件太大",
    415: "不支持的文件格式",
    422: "参数错误",
    429: "请求过于频繁",
    500: "服务器内部错误",
    502: "服务暂时不可用",
    503: "服务暂时不可用",
    409: "积分不足",
    406: "文件大小超过15M",
    407: "图片分辨率小于70",
}

class KoukoutuBackgroundRemoval:
    """
    Koukoutu Background Removal Node for ComfyUI
    Uses Koukoutu API to remove backgrounds from images
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
            },
            "optional": {
                "model_key_name": (["通用抠图模型", "印花专抠模型"], {
                    "default": "通用抠图模型",
                    'placeholder': '选择模型'
                }),
                "output_format": (["png", "webp"], {
                    "default": "webp"
                }),
                "crop": ("BOOLEAN", {
                    "default": False,
                    "label_on": "启用裁切到边",
                    "label_off": "禁用裁切到边"
                }),
                "stamp_crop": ("BOOLEAN", {
                    "default": False,
                    "label_on": "启用印花自动识别裁切",
                    "label_off": "禁用印花自动识别裁切",
                }),
                "border": (["不增强", "标准增强", "高度增强"], {
                    "default": "不增强"
                }),
                "output_response": ("STRING", {
                    "default": 'file',
                    "hidden": True
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "remove_background"
    CATEGORY = "image/koukoutu"
    DESCRIPTION = "使用 Koukoutu API 移除图像背景"
    
    def remove_background(self, image, api_key, model_key_name, output_format="png", crop=False, stamp_crop=False, border='不增强', output_response='file', error_num=0):
        """
        Remove background from image using Koukoutu API
        """
        try:
            # Validate API key
            validated_api_key = validate_api_key(api_key)
            # Convert ComfyUI image tensor to PIL Image
            pil_image = tensor_to_pil(image)
            
            # Save image to temporary file for upload
            temp_path = save_temp_image(pil_image, 'PNG')
            
            try:
                # Prepare API request
                api_url = "https://sync.koukoutu.com/v1/create"
                
                headers = {
                    'Authorization': f"Bearer {validated_api_key}"
                }

                model_key_dict = {
                    "通用抠图模型": "background-removal",
                    "印花专抠模型": "stamp-background-removal",
                }
                model_key = model_key_dict.get(model_key_name, "background-removal")

                border_dict = {
                    "不增强": "0",
                    "标准增强": "1",
                    "高度增强": "2"
                }
                data = {
                    'model_key': model_key,
                    'output_format': output_format,
                    'crop': '1' if crop else '0',
                    'stamp_crop': '1' if stamp_crop else '0',
                    'border': border_dict.get(border, "0"),
                    'response': output_response
                }
                # Open and upload the image file
                files = {
                    'image_file': ('image.jpg', open(temp_path, 'rb'), 'image/jpg')
                }
                # Make API request
                response = requests.post(
                    api_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=60
                )
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type and output_response == 'file':
                    json_response = response.json()
                    code = json_response.get('code', 200)
                    if code in [500, 502, 503, 504] and error_num <= 5:
                        return self.remove_background(image, api_key, model_key_name, output_format, crop, stamp_crop, border, output_response, error_num + 1)
                    else:
                        raise Exception(code_dict.get(code, f"API 错误: {json_response.get('message', '未知错误')}"))
                image_data = response.content
                result_image = Image.open(io.BytesIO(image_data))
                result_tensor = pil_to_tensor(result_image)
                return (result_tensor,)
            finally:
                # Clean up temporary file
                cleanup_temp_file(temp_path)
                
        except requests.RequestException as e:
            if error_num <= 5:
                return self.remove_background(image, api_key, model_key_name, output_format, crop, stamp_crop, border, output_response, error_num + 1)
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            raise Exception(f"背景移除失败: {str(e)}")
    
    @classmethod
    def IS_CHANGED(cls, image, api_key, model_key_name="通用抠图模型", output_format="png", crop=False, stamp_crop=False, border='不增强', output_response='file'):
        """
        This method helps ComfyUI determine when to re-execute the node
        Returns a hash of the input parameters to enable intelligent caching
        """
        import hashlib
        
        # Convert image tensor to a hashable representation
        if image is not None:
            # Create a hash based on image data
            image_hash = hashlib.md5(image.cpu().numpy().tobytes()).hexdigest()[:16]
        else:
            image_hash = "no_image"
        
        # Create a combined hash of all parameters
        params_str = f"{image_hash}_{api_key[:8] if api_key else 'no_key'}_{model_key_name}_{output_format}_{crop}_{stamp_crop}_{border}_{output_response}"
        param_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
        
        return param_hash
