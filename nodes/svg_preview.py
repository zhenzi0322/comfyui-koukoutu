def normalize_svg(svg_text):
    """
    规范化 SVG 文本：去掉 BOM 与从聊天/文档复制时带上的 markdown 代码围栏

    Args:
        svg_text: 原始输入的 SVG 文本

    Returns:
        str: 可直接用于 <img> 渲染的 SVG 文本
    """
    text = (svg_text or '').strip().lstrip('\ufeff')

    # 兼容 ```svg ... ``` 代码块
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        if text.rstrip().endswith('```'):
            text = text.rstrip()[:-3]
        text = text.strip()

    return text


class KoukoutuSVGPreview:
    """
    Koukoutu SVG 预览节点
    在节点面板内直接渲染 SVG 矢量图，纯预览、不产生输出
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "粘贴 SVG 源码，或把 SVG 输出连接到本节点"
                }),
            },
        }
    
    # 无下游连接时也要执行，执行后通过 ui 数据把 SVG 回传前端渲染
    OUTPUT_NODE = True
    RETURN_TYPES = ()
    FUNCTION = "preview_svg"
    CATEGORY = "image/koukoutu"
    DESCRIPTION = "在节点内预览 SVG 矢量图（无需渲染依赖）"
    # 节点搜索关键词
    SEARCH_ALIASES = [
        "svg预览",
        "预览svg",
        "矢量图预览",
        "svg preview",
        "vector preview",
        "vector",
        "svg",
    ]
    
    def preview_svg(self, svg):
        """
        SVG 预览：
        1. 规范化 SVG 文本（去 BOM、去 markdown 代码围栏）
        2. 校验是否包含 <svg> 标签
        3. 通过 ui 数据把文本回传前端，供节点内预览（连线输入同样生效）
        """
        text = normalize_svg(svg)
        if not text or '<svg' not in text:
            return {"ui": {"svg": [""]}, "result": ()}

        return {"ui": {"svg": [text]}, "result": ()}
