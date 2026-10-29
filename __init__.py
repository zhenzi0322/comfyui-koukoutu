"""
Koukoutu ComfyUI Nodes
Background removal and other AI processing nodes using Koukoutu API
"""

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Try to load the main background removal node
try:
    from .nodes.background_removal import KoukoutuBackgroundRemoval
    NODE_CLASS_MAPPINGS["KoukoutuBackgroundRemoval"] = KoukoutuBackgroundRemoval
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuBackgroundRemoval"] = "抠抠图-抠图功能"
    print("Koukoutu Background Removal node loaded successfully")
except Exception as e:
    print(f"Failed to load Background Removal node: {e}")

try:
    from .nodes.stamp_crop import KoukoutuStampCrop
    NODE_CLASS_MAPPINGS["KoukoutuStampCrop"] = KoukoutuStampCrop
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuStampCrop"] = "抠抠图-印花定位裁切功能"
    print("Koukoutu Stamp Crop node loaded successfully")
except Exception as e:
    print(f"Failed to load Stamp Crop node: {e}")

try:
    from .nodes.image_to_image import KoukoutuImageToImage
    NODE_CLASS_MAPPINGS["KoukoutuImageToImage"] = KoukoutuImageToImage
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuImageToImage"] = "抠抠图-图生图功能"
    print("Koukoutu Image To Image node loaded successfully")
except Exception as e:
    print(f"Failed to load Image To Image node: {e}")

try:
    from .nodes.image_extract import KoukoutuImageExtract
    NODE_CLASS_MAPPINGS["KoukoutuImageExtract"] = KoukoutuImageExtract
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuImageExtract"] = "抠抠图-标准印花提取功能"
    print("Koukoutu Image Extract node loaded successfully")
except Exception as e:
    print(f"Failed to load Image Extract node: {e}")

try:
    from .nodes.image_extract_v2 import KoukoutuImageExtractV2
    NODE_CLASS_MAPPINGS["KoukoutuImageExtractV2"] = KoukoutuImageExtractV2
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuImageExtractV2"] = "抠抠图-中阶印花提取功能"
    print("Koukoutu Image Extract V2 node loaded successfully")
except Exception as e:
    print(f"Failed to load Image Extract V2 node: {e}")

try:
    from .nodes.watermark_removal import KoukoutuWatermarkRemoval
    NODE_CLASS_MAPPINGS["KoukoutuWatermarkRemoval"] = KoukoutuWatermarkRemoval
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuWatermarkRemoval"] = "抠抠图-去水印功能"
    print("Koukoutu Watermark Removal node loaded successfully")
except Exception as e:
    print(f"Failed to load Watermark Removal node: {e}")

try:
    from .nodes.ai_shadow import KoukoutuAIShadow
    NODE_CLASS_MAPPINGS["KoukoutuAIShadow"] = KoukoutuAIShadow
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuAIShadow"] = "抠抠图-AI 生成阴影图功能"
    print("Koukoutu AI Shadow node loaded successfully")
except Exception as e:
    print(f"Failed to load AI Shadow node: {e}")

try:
    from .nodes.upscale import KoukoutuUpscale
    NODE_CLASS_MAPPINGS["KoukoutuUpscale"] = KoukoutuUpscale
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuUpscale"] = "抠抠图-通用放大变清晰功能"
    print("Koukoutu Upscale node loaded successfully")
except Exception as e:
    print(f"Failed to load Upscale node: {e}")

try:
    from .nodes.outpaint import KoukoutuOutpaint
    NODE_CLASS_MAPPINGS["KoukoutuOutpaint"] = KoukoutuOutpaint
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuOutpaint"] = "抠抠图-扩图功能"
    print("Koukoutu Outpaint node loaded successfully")
except Exception as e:
    print(f"Failed to load Outpaint node: {e}")

try:
    from .nodes.image_to_svg import KoukoutuImageToSVG
    NODE_CLASS_MAPPINGS["KoukoutuImageToSVG"] = KoukoutuImageToSVG
    # 显示名内带上核心关键词，兼容不支持 SEARCH_ALIASES 的旧版前端搜索
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuImageToSVG"] = "抠抠图-图片转SVG功能（位图转矢量）"
    print("Koukoutu Image To SVG node loaded successfully")
except Exception as e:
    print(f"Failed to load Image To SVG node: {e}")

try:
    from .nodes.image_extract_v3 import KoukoutuImageExtractV3
    NODE_CLASS_MAPPINGS["KoukoutuImageExtractV3"] = KoukoutuImageExtractV3
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuImageExtractV3"] = "抠抠图-高阶印花提取功能"
    print("Koukoutu Image Extract V3 node loaded successfully")
except Exception as e:
    print(f"Failed to load Image Extract V3 node: {e}")

try:
    from .nodes.svg_preview import KoukoutuSVGPreview
    NODE_CLASS_MAPPINGS["KoukoutuSVGPreview"] = KoukoutuSVGPreview
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuSVGPreview"] = "抠抠图-SVG预览功能（矢量图预览）"
    print("Koukoutu SVG Preview node loaded successfully")
except Exception as e:
    print(f"Failed to load SVG Preview node: {e}")

if not NODE_CLASS_MAPPINGS:
    print("No Koukoutu nodes could be loaded. Please check your dependencies.")

# 前端扩展目录（节点面板的输入控件动态显隐）
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
