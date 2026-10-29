import { app } from "../../scripts/app.js";

// SVG 预览节点：在节点内部用自定义 widget 渲染 SVG，无需任何渲染依赖
const NODE_NAME = "KoukoutuSVGPreview";
const PREVIEW_WIDGET = "svg_preview";
const PREVIEW_HEIGHT = 384; // 有 SVG 时的预览区高度
const PLACEHOLDER_HEIGHT = 44; // 无 SVG 时只保留一行占位
const DEFAULT_NODE_WIDTH = 420; // 新建节点时的默认宽度，让预览更宽
const DEBOUNCE_MS = 250;
const PADDING = 8;
const CHECKER_CELL = 8;

function getPreviewWidget(node) {
  return node.widgets?.find((widget) => widget.name === PREVIEW_WIDGET);
}

function getSvgWidget(node) {
  return node.widgets?.find((widget) => widget.name === "svg");
}

// 与后端 normalize_svg 保持一致：去 BOM、去 markdown 代码围栏
function normalizeSvg(text) {
  let svg = (text || "").replace(/^\uFEFF/, "").trim();
  if (svg.startsWith("```")) {
    const lines = svg.split("\n");
    svg = lines.slice(1).join("\n");
    if (svg.trimEnd().endsWith("```")) {
      svg = svg.trimEnd().slice(0, -3);
    }
    svg = svg.trim();
  }
  return svg;
}

function hasPreviewImage(node) {
  const image = node.__koukoutuSvgImage;
  return !!(image && image.width && image.height);
}

// 不同版本的 executed 消息结构不一致，逐个兼容
function extractSvg(payload) {
  if (!payload || typeof payload !== "object") return null;

  const direct = payload.svg ?? payload.text;
  if (Array.isArray(direct) && typeof direct[0] === "string") return direct[0];
  if (typeof direct === "string") return direct;

  for (const key of ["output", "outputs", "ui", "result"]) {
    const nested = extractSvg(payload[key]);
    if (nested) return nested;
  }
  return null;
}

// 占位与预览状态切换时调整节点高度，其余情况不打断用户手动拉伸
function updateNodeSize(node) {
  const targetHeight = hasPreviewImage(node) ? PREVIEW_HEIGHT : PLACEHOLDER_HEIGHT;

  // 部分前端版本不读 widget.computeSize，改用 options.height 决定绘制高度，两边同步
  const previewWidget = getPreviewWidget(node);
  if (previewWidget) {
    previewWidget.options = previewWidget.options || {};
    previewWidget.options.height = targetHeight;
  }

  if (node.__koukoutuPreviewHeight === targetHeight) {
    node.setDirtyCanvas(true, true);
    return;
  }

  node.__koukoutuPreviewHeight = targetHeight;
  // 只在高度不足时撑开，不主动缩小，避免覆盖用户手动拖拽的尺寸
  const requiredHeight = node.computeSize()[1];
  if (node.size[1] < requiredHeight) {
    node.setSize([node.size[0], requiredHeight]);
  }
  node.setDirtyCanvas(true, true);
}

function renderSvg(node, rawText) {
  const svg = normalizeSvg(rawText);
  // 一次执行可能被 onExecuted 与 executed 事件重复触发，相同内容只渲染一次
  if (node.__koukoutuSvgSource === svg) return;
  node.__koukoutuSvgSource = svg;

  if (!svg || !svg.includes("<svg")) {
    node.__koukoutuSvgImage = null;
    node.__koukoutuSvgError = svg ? "内容不是 SVG" : "无 SVG 内容";
    updateNodeSize(node);
    node.setDirtyCanvas(true, true);
    return;
  }

  const image = new Image();
  image.onload = () => {
    node.__koukoutuSvgImage = image;
    node.__koukoutuSvgError = "";
    updateNodeSize(node);
    node.setDirtyCanvas(true, true);
  };
  image.onerror = () => {
    node.__koukoutuSvgImage = null;
    node.__koukoutuSvgError = "SVG 解析失败";
    updateNodeSize(node);
    node.setDirtyCanvas(true, true);
  };
  image.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

function scheduleRender(node) {
  if (node.__koukoutuSvgTimer) clearTimeout(node.__koukoutuSvgTimer);
  node.__koukoutuSvgTimer = setTimeout(() => {
    renderSvg(node, getSvgWidget(node)?.value);
  }, DEBOUNCE_MS);
}

// 棋盘格背景，便于看出 SVG 的透明区域
function drawCheckerboard(ctx, x, y, width, height) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, width, height);
  ctx.clip();

  ctx.fillStyle = "#2b2b2b";
  ctx.fillRect(x, y, width, height);

  ctx.fillStyle = "#383838";
  for (let row = 0; row * CHECKER_CELL < height; row++) {
    for (let col = row % 2; col * CHECKER_CELL < width; col += 2) {
      ctx.fillRect(
        x + col * CHECKER_CELL,
        y + row * CHECKER_CELL,
        CHECKER_CELL,
        CHECKER_CELL
      );
    }
  }
  ctx.restore();
}

// 无 SVG 内容时的占位条
function drawPlaceholder(ctx, x, y, width, height, message) {
  ctx.save();
  ctx.fillStyle = "#2b2b2b";
  ctx.fillRect(x, y, width, height);

  ctx.strokeStyle = "#3f3f3f";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.strokeRect(x + 0.5, y + 0.5, Math.max(width - 1, 1), Math.max(height - 1, 1));
  ctx.setLineDash([]);

  ctx.fillStyle = "#888888";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(message || "无 SVG 内容", x + width / 2, y + height / 2);
  ctx.restore();
}

function createPreviewWidget(node) {
  return {
    name: PREVIEW_WIDGET,
    type: "koukoutu_svg_preview",
    value: "",
    serialize: false,
    options: { height: PLACEHOLDER_HEIGHT },
    computeSize(width) {
      return [width, hasPreviewImage(node) ? PREVIEW_HEIGHT : PLACEHOLDER_HEIGHT];
    },
    draw(ctx, widgetNode, widgetWidth, y, H) {
      // 部分前端版本传入的 H 是默认 widget 高度，优先用自身配置的高度
      const baseHeight = Math.max(H, this?.options?.height ?? H);
      // widgetWidth 由 LiteGraph 传入，可能大于节点实际宽度，取两者较小值避免溢出
      const totalWidth = Math.min(widgetWidth, widgetNode.size?.[0] ?? widgetWidth);
      // 节点被拖大时，预览区跟随节点剩余高度一起放大；最小不低于配置高度
      const nodeHeight = widgetNode.size?.[1] ?? 0;
      const availableHeight = Math.max(baseHeight, nodeHeight - y - PADDING);

      const x = PADDING;
      const width = Math.max(totalWidth - PADDING * 2, 16);
      const top = y + PADDING / 2;
      const height = Math.max(availableHeight - PADDING, 16);

      ctx.save();
      ctx.beginPath();
      ctx.rect(0, y, totalWidth, availableHeight);
      ctx.clip();

      if (!hasPreviewImage(widgetNode)) {
        drawPlaceholder(ctx, x, top, width, height, widgetNode.__koukoutuSvgError);
        ctx.restore();
        return;
      }

      drawCheckerboard(ctx, x, top, width, height);

      const image = widgetNode.__koukoutuSvgImage;
      const scale = Math.min(width / image.width, height / image.height);
      const drawWidth = image.width * scale;
      const drawHeight = image.height * scale;
      ctx.drawImage(
        image,
        x + (width - drawWidth) / 2,
        top + (height - drawHeight) / 2,
        drawWidth,
        drawHeight
      );
      ctx.restore();
    },
  };
}

function setupPreview(node) {
  if (!node.widgets) return;

  if (!node.widgets.some((widget) => widget.name === PREVIEW_WIDGET)) {
    const widget = createPreviewWidget(node);
    if (typeof node.addCustomWidget === "function") {
      node.addCustomWidget(widget);
    } else {
      node.widgets.push(widget);
    }
  }

  const svgWidget = getSvgWidget(node);
  if (svgWidget && !svgWidget.__koukoutuWrapped) {
    const originalCallback = svgWidget.callback;
    svgWidget.callback = function (value, ...args) {
      const result = originalCallback?.apply(this, [value, ...args]);
      scheduleRender(node);
      return result;
    };
    svgWidget.__koukoutuWrapped = true;
  }

  // 新建节点时给预览区一个更合适的宽度
  if (node.size[0] < DEFAULT_NODE_WIDTH) {
    node.setSize([DEFAULT_NODE_WIDTH, node.size[1]]);
  }

  // 新建节点时按“无内容”的占位高度收住预览区
  node.__koukoutuPreviewHeight = null;
  updateNodeSize(node);
  requestAnimationFrame(() => renderSvg(node, svgWidget?.value));
}

app.registerExtension({
  name: "koukoutu.SVGPreview.InlineRenderer",
  // 兜底：部分版本不会回调 onExecuted，直接监听 executed 事件拿 ui 数据
  async setup() {
    app.api.addEventListener("executed", ({ detail }) => {
      const node = app.graph.getNodeById(detail.display_node ?? detail.node);
      if (!node || node.comfyClass !== NODE_NAME) return;

      const svg = extractSvg(detail.output);
      if (svg) renderSvg(node, svg);
    });
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_NAME) return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);
      setupPreview(this);
      return result;
    };

    // 加载已保存的工作流时，用节点上保存的 SVG 文本恢复预览
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const result = onConfigure?.apply(this, arguments);
      setTimeout(() => renderSvg(this, getSvgWidget(this)?.value), 0);
      return result;
    };

    // 执行完成后后端会通过 ui 回传规范化后的 SVG，连线输入同样可以预览
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      const result = onExecuted?.apply(this, arguments);
      const svg = extractSvg(message);
      if (svg) {
        renderSvg(this, svg);
      } else {
        console.warn("[Koukoutu] SVG 预览未收到数据", message);
      }
      return result;
    };
  },
});
