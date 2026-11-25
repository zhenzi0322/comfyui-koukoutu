import os
import time
import uuid

import numpy as np
import torch
from PIL import Image


# 预览尺寸与输出保持一致；仅当平铺图最长边超过该值时等比缩小，避免巨图拖慢前端
MAX_PREVIEW_SIZE = 8192


def tile_tensor(image, tiles, grid_lines):
    """
    把图像沿宽、高方向各重复 tiles 次，得到 N×N 平铺图
    
    Args:
        image: ComfyUI 图像张量 [B, H, W, C]
        tiles: 单边重复次数，3 表示九宫格
        grid_lines: 是否在重复单元之间画分隔线
        
    Returns:
        tensor: 平铺后的图像张量 [B, H*tiles, W*tiles, C]
    """
    tiled = torch.cat([image] * tiles, dim=2)   # 横向重复
    tiled = torch.cat([tiled] * tiles, dim=1)   # 纵向重复

    if grid_lines:
        arr = tiled.cpu().numpy().copy()
        height, width = arr.shape[1], arr.shape[2]
        step_h = max(height // tiles, 1)
        step_w = max(width // tiles, 1)
        # 只画内部的分隔线，颜色通道置黑，保留 alpha
        arr[:, step_h::step_h, :, :3] = 0.0
        arr[:, :, step_w::step_w, :3] = 0.0
        tiled = torch.from_numpy(arr)
    return tiled


def save_preview_images(tensor):
    """
    把平铺结果写入 ComfyUI 临时目录，并返回 ui.images 结构供前端渲染
    
    Args:
        tensor: 平铺后的图像张量 [B, H, W, C]
        
    Returns:
        list: [{"filename": ..., "subfolder": "", "type": "temp"}]
    """
    try:
        import folder_paths
    except ImportError:
        # 脱离 ComfyUI 环境时跳过落盘，仍返回图像结果
        print("[Koukoutu] 未找到 folder_paths，跳过九宫格预览落盘")
        return []

    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)

    results = []
    stamp = time.strftime('%Y%m%d_%H%M%S')
    for index in range(tensor.shape[0]):
        arr = (tensor[index].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        preview = Image.fromarray(arr)
        # 正常尺寸不缩放，保证节点内标注的尺寸与输出一致
        if max(preview.size) > MAX_PREVIEW_SIZE:
            preview.thumbnail((MAX_PREVIEW_SIZE, MAX_PREVIEW_SIZE), Image.LANCZOS)
        file_name = f"koukoutu_tile_{stamp}_{index}_{uuid.uuid4().hex[:8]}.png"
        preview.save(os.path.join(temp_dir, file_name), format='PNG')
        results.append({
            "filename": file_name,
            "subfolder": "",
            "type": "temp",
        })
    return results


class KoukoutuTilePreview:
    """
    Koukoutu 九宫格平铺预览节点
    把输入图像按 N×N 重复拼接，在节点内直接展示，方便检查四方连续图接缝是否连续
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "tiles": ("INT", {
                    "default": 3,
                    "min": 2,
                    "max": 6,
                    "step": 1,
                    "tooltip": "单边重复次数，3 即九宫格",
                }),
                "grid_lines": ("BOOLEAN", {
                    "default": False,
                    "label_on": "显示分隔线（便于确认重复单元）",
                    "label_off": "不显示分隔线（便于观察接缝）",
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "tile_preview"
    # 无下游连接时也要执行，执行后通过 ui.images 把平铺图回传前端展示
    OUTPUT_NODE = True
    CATEGORY = "image/koukoutu"
    DESCRIPTION = "把图像按 N×N 平铺并在节点内展示，用于检查四方连续图的接缝是否连续"
    # 节点搜索关键词
    SEARCH_ALIASES = [
        "九宫格",
        "平铺预览",
        "四方连续预览",
        "接缝检查",
        "无缝检查",
        "tile preview",
        "seamless check",
        "pattern preview",
    ]
    
    def tile_preview(self, image, tiles=3, grid_lines=False):
        """
        九宫格平铺预览：
        1. 沿宽高方向各重复 tiles 次，拼成 N×N 平铺图
        2. 可选在重复单元之间画分隔线
        3. 平铺图落到 ComfyUI 临时目录，通过 ui.images 在节点内展示
        4. 同时把平铺图片作为 IMAGE 输出，可继续接保存节点
        """
        tiled = tile_tensor(image, tiles, grid_lines)
        previews = save_preview_images(tiled)

        if previews:
            return {"ui": {"images": previews}, "result": (tiled,)}
        return {"ui": {}, "result": (tiled,)}
