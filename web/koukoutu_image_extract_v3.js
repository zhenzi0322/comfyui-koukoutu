import { app } from "../../scripts/app.js";

// 高阶印花提取节点的尺寸参数动态显隐：
// size_mode = 按比例 -> 显示 size / resolution
// size_mode = 按宽高 -> 显示 w / h
const NODE_NAME = "KoukoutuImageExtractV3";
const MODE_WIDGET = "size_mode";
const RATIO_WIDGETS = ["size", "resolution"];
const SIZE_WIDGETS = ["w", "h"];

function findWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

// 隐藏 widget：保留原类型与尺寸计算函数，便于后续恢复
function hideWidget(widget) {
  if (!widget || widget.__koukoutuHidden) return;

  widget.__koukoutuOrigType = widget.type;
  widget.__koukoutuOrigComputeSize = widget.computeSize;
  widget.type = "hidden";
  widget.computeSize = () => [0, -4];
  widget.__koukoutuHidden = true;
}

function showWidget(widget) {
  if (!widget || !widget.__koukoutuHidden) return;

  widget.type = widget.__koukoutuOrigType;
  if (widget.__koukoutuOrigComputeSize) {
    widget.computeSize = widget.__koukoutuOrigComputeSize;
  } else {
    delete widget.computeSize;
  }
  delete widget.__koukoutuOrigType;
  delete widget.__koukoutuOrigComputeSize;
  delete widget.__koukoutuHidden;
}

function refreshVisibility(node) {
  const modeWidget = findWidget(node, MODE_WIDGET);
  if (!modeWidget) return;

  const useCustomSize = modeWidget.value === "按宽高";

  for (const name of RATIO_WIDGETS) {
    const widget = findWidget(node, name);
    useCustomSize ? hideWidget(widget) : showWidget(widget);
  }
  for (const name of SIZE_WIDGETS) {
    const widget = findWidget(node, name);
    useCustomSize ? showWidget(widget) : hideWidget(widget);
  }

  // 隐藏/显示后重新计算节点高度，避免留下空白区域
  node.setSize([node.size[0], node.computeSize()[1]]);
  node.setDirtyCanvas(true, true);
}

function setupDynamicWidgets(node) {
  const modeWidget = findWidget(node, MODE_WIDGET);
  if (!modeWidget) return;

  const originalCallback = modeWidget.callback;
  modeWidget.callback = function (value, ...args) {
    const result = originalCallback?.apply(this, [value, ...args]);
    refreshVisibility(node);
    return result;
  };

  // 等 widgets 布局完成后再做首次刷新，避免读取到未初始化的尺寸
  requestAnimationFrame(() => refreshVisibility(node));
}

app.registerExtension({
  name: "koukoutu.ImageExtractV3.DynamicWidgets",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_NAME) return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);
      setupDynamicWidgets(this);
      return result;
    };

    // 加载已保存的工作流时，按保存的 size_mode 恢复显隐状态
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const result = onConfigure?.apply(this, arguments);
      setTimeout(() => refreshVisibility(this), 0);
      return result;
    };
  },
});
