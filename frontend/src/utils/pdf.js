import { PDFDocument, degrees, rgb } from "pdf-lib";
import * as fontkit from "fontkit";

// 全局缓存字体字节，避免重复 fetch
let cachedFontBytes = null;
let cachedBoldFontBytes = null;

// evalReport.js

/**
 * data 示例：
 * {
 *   indicator: [{ key, value }, ...],
 *   runtimeInfo: { cpu, memory, runtime },
 *   evalId,
 *   evalTime,
 *   evalName,
 *   organizer
 * }
 */
export async function generateEvalReport(data) {
  // 第一次调用 fetch 字体文件
  if (!cachedFontBytes) {
    const fontUrl = "/SourceHanSansCN-Regular.ttf";
    const boldFontUrl = "/SourceHanSansCN-Bold.ttf";
    [cachedFontBytes, cachedBoldFontBytes] = await Promise.all([
      fetch(fontUrl).then(res => res.arrayBuffer()),
      fetch(boldFontUrl).then(res => res.arrayBuffer()),
    ]);
  }

  const pdfDoc = await PDFDocument.create();
  const page = pdfDoc.addPage([595, 842]); // A4
  pdfDoc.registerFontkit(fontkit);
  const { width, height } = page.getSize();

  const font = await pdfDoc.embedFont(cachedFontBytes);
  const fontBold = await pdfDoc.embedFont(cachedBoldFontBytes);

  let y = 780;
  const left = 60;

  /* ============================
        1. 居中大标题
  ============================ */
  const title = "Align Eval 算法评测报告";
  const titleSize = 26;
  const titleWidth = font.widthOfTextAtSize(title, titleSize);
  page.drawText(title, {
    x: (width - titleWidth) / 2,
    y,
    size: titleSize,
    font,
    color: rgb(0, 0, 0),
  });

  y -= 50;

  /* ============================
      2. Word 风格基础信息表格
  ============================ */

  const infoFields = [
    ["评测编号", data.evalId],
    ["评测名称", data.evalName],
    ["评测时间", data.evalTime],
    ["发起人", data.organizer],
  ];

  const tableX = left;
  const tableWidth = width - left * 2;
  const col1Width = 120; // 左列固定宽度
  const rowH = 28;

  drawWordStyleTable(page, {
    x: tableX,
    y,
    width: tableWidth,
    col1Width,
    rows: infoFields,
    rowHeight: rowH,
    font,
  });

  y -= infoFields.length * rowH + 50;

  /* ============================
       3. 关键指标表格
  ============================ */
  page.drawText("一、关键指标结果", {
    x: left,
    y,
    size: 18,
    font,
  });

  y -= 30;

  drawSimpleTable(page, {
    x: left,
    y,
    width: tableWidth,
    headers: ["指标名称", "数值"],
    rows: data.indicator.map(i => [i.key, String(i.value)]),
    rowHeight: 26,
    font,
  });

  y -= (data.indicator.length + 1) * 26 + 50;

  /* ============================
       4. 系统运行信息表格
  ============================ */
  page.drawText("二、系统运行信息", {
    x: left,
    y,
    size: 18,
    font,
  });

  y -= 30;

  drawSimpleTable(page, {
    x: left,
    y,
    width: tableWidth,
    headers: ["运行项", "数值"],
    rows: [
      ["CPU 使用率（%）", data.runtimeInfo.cpu],
      ["内存占用（MB）", data.runtimeInfo.memory],
      ["运行耗时（s）", data.runtimeInfo.runtime],
    ],
    rowHeight: 26,
    font,
  });

  /* ============================
       5. 页脚
  ============================ */
  page.drawText("由 Align Eval 平台自动生成", {
    x: left,
    y: 30,
    size: 10,
    font,
    color: rgb(0.5, 0.5, 0.5),
  });

  const watermarkText = "Align Eval 分析报告";

  const wmFontSize = 72;
  const wmWidth = fontBold.widthOfTextAtSize(watermarkText, wmFontSize);

  // 透明度 0.08（可调）
  // 旋转角度 -30°（可调）
  page.drawText(watermarkText, {
    x: (width - wmWidth) / 2 + 100,
    y: height / 4,
    size: wmFontSize,
    font: fontBold,
    color: rgb(0.75, 0.75, 0.75),
    opacity: 0.3,
    rotate: degrees(45),
  });

  // 导出 PDF Blob
  const pdfBytes = await pdfDoc.save();
  return new Blob([pdfBytes], { type: "application/pdf" });
}

/* ========== Word 风格表格 ========== */
function drawWordStyleTable(
  page,
  { x, y, width, col1Width, rows, rowHeight, font }
) {
  const border = rgb(0.2, 0.2, 0.2);

  rows.forEach((row, i) => {
    const rowY = y - rowHeight * i;

    // 边框矩形
    page.drawRectangle({
      x,
      y: rowY - rowHeight,
      width,
      height: rowHeight,
      borderWidth: 1,
      borderColor: border,
    });

    // 左列竖线
    page.drawLine({
      start: { x: x + col1Width, y: rowY },
      end: { x: x + col1Width, y: rowY - rowHeight },
      thickness: 1,
      color: border,
    });

    // 绘制 label
    page.drawText(row[0], {
      x: x + 8,
      y: rowY - rowHeight + 8,
      size: 12,
      font,
    });

    // 绘制 value
    page.drawText(String(row[1] ?? ""), {
      x: x + col1Width + 8,
      y: rowY - rowHeight + 8,
      size: 12,
      font,
    });
  });
}

/* ========== 普通横向表格（指标 & runtime） ========== */
function drawSimpleTable(
  page,
  { x, y, width, headers, rows, rowHeight, font }
) {
  const colW = width / headers.length;

  // 表头底灰
  page.drawRectangle({
    x,
    y: y - rowHeight,
    width,
    height: rowHeight,
    color: rgb(0.92, 0.92, 0.92),
  });

  // 表头文本
  headers.forEach((h, i) => {
    page.drawText(h, {
      x: x + colW * i + 5,
      y: y - rowHeight + 8,
      size: 12,
      font,
    });
  });

  // 内容行
  rows.forEach((row, r) => {
    const rowY = y - rowHeight * (r + 1);

    row.forEach((cell, c) => {
      page.drawText(String(cell), {
        x: x + colW * c + 5,
        y: rowY - rowHeight + 8,
        size: 12,
        font,
      });
    });

    // 画横线
    page.drawLine({
      start: { x, y: rowY - rowHeight },
      end: { x: x + width, y: rowY - rowHeight },
      thickness: 0.5,
      color: rgb(0.7, 0.7, 0.7),
    });
  });
}
