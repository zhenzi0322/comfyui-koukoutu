"""
Utility functions for Koukoutu ComfyUI nodes
"""

import torch
import numpy as np
from PIL import Image
import io
import tempfile
import os


def tensor_to_pil(tensor):
    """
    Convert ComfyUI image tensor to PIL Image
    
    Args:
        tensor: ComfyUI image tensor [batch, height, width, channels] with values 0-1
        
    Returns:
        PIL Image
    """
    if len(tensor.shape) == 4:
        # Take first image from batch
        image_tensor = tensor[0]
    else:
        image_tensor = tensor
        
    # Convert from tensor to numpy array and scale to 0-255
    image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
    return Image.fromarray(image_np)


def pil_to_tensor(pil_image):
    """
    Convert PIL Image to ComfyUI tensor format
    
    Args:
        pil_image: PIL Image
        
    Returns:
        tensor: ComfyUI image tensor [1, height, width, channels] with values 0-1
    """
    # Ensure image has RGBA channels for transparency support
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')
    
    # Convert PIL Image to tensor format
    image_np = np.array(pil_image).astype(np.float32) / 255.0
    return torch.from_numpy(image_np).unsqueeze(0)  # Add batch dimension


def save_temp_image(pil_image, format='PNG'):
    """
    Save PIL image to temporary file
    
    Args:
        pil_image: PIL Image to save
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        str: Path to temporary file
    """
    suffix = f'.{format.lower()}'
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    pil_image.save(temp_file.name, format)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path):
    """
    Safely remove temporary file
    
    Args:
        file_path: Path to file to remove
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def validate_api_key(api_key):
    """
    Validate API key format
    
    Args:
        api_key: API key string
        
    Returns:
        str: Cleaned API key
        
    Raises:
        ValueError: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API Key 不能为空")
    
    cleaned_key = api_key.strip()
    if not cleaned_key:
        raise ValueError("API Key 不能为空")
    
    return cleaned_key


def handle_api_response(response):
    """
    Handle API response and extract image data
    
    Args:
        response: requests.Response object
        
    Returns:
        bytes: Image data
        
    Raises:
        Exception: If response indicates error
    """
    if response.status_code != 200:
        error_msg = f"API 请求失败，状态码: {response.status_code}"
        try:
            error_detail = response.json()
            error_msg += f", 错误详情: {error_detail}"
        except:
            error_msg += f", 响应内容: {response.text[:200]}"
        raise Exception(error_msg)
    
    content_type = response.headers.get('content-type', '')
    
    if 'application/json' in content_type:
        # Handle JSON response
        json_response = response.json()
        if 'error' in json_response:
            raise Exception(f"API 错误: {json_response['error']}")
        elif 'url' in json_response:
            # Download image from URL
            import requests
            image_response = requests.get(json_response['url'], timeout=30)
            if image_response.status_code != 200:
                raise Exception(f"下载处理后的图像失败: {image_response.status_code}")
            return image_response.content
        else:
            raise Exception(f"未知的 JSON 响应格式: {json_response}")
    elif 'image' in content_type:
        # Direct image response
        return response.content
    else:
        raise Exception(f"未知的响应类型: {content_type}")
