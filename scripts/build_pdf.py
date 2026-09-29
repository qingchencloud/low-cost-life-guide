#!/usr/bin/env python3
"""Build the reading edition PDF from data/cases.json.

The PDF is generated from the same JSON that powers the website, so the web
index and downloadable edition share one source of truth.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import platform
import sys
from pathlib import Path
from typing import Iterable

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cases.json"
OUT = ROOT / "downloads"

CATEGORY_ORDER = [
    "消费与财务",
    "职场与学习",
    "工具与效率",
    "信息与隐私",
    "健康误区",
    "低效决策",
    "关系与沟通",
]
CATEGORY_INTROS = {
    "消费与财务": "把价格、收入和现金流放回同一张账里，识别“便宜”背后的锁定成本。",
    "职场与学习": "把忙碌、证书和在线时长还原成可验收的结果与机会成本。",
    "工具与效率": "工具服务于任务；当配置、迁移和追新成为任务本身，就该停下来复盘。",
    "信息与隐私": "传播速度不等于证据强度，公开范围也不等于可控范围。",
    "健康误区": "先识别风险和求助边界，再谈习惯、效率和自我管理。",
    "低效决策": "把后悔拆成变量，用小实验、退出条件和可迁移资产减少重复下注。",
    "关系与沟通": "边界是自己的行动，沟通是可验证的约定，不靠制造压力测试关系。",
}

FONT_CANDIDATES = {
    "regular": [
        Path(r"C:\Windows\Fonts\Deng.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ],
    "bold": [
        Path(r"C:\Windows\Fonts\Dengb.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
    ],
}


def register_fonts() -> tuple[str, str]:
    def cid_fallback() -> tuple[str, str]:
        # STSong-Light is a portable CID font available in ReportLab itself;
        # unlike Helvetica it can encode Chinese text on Linux CI runners.
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            return "STSong-Light", "STSong-Light"
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"Warning: built-in Chinese font unavailable ({exc}); using Helvetica.")
            return "Helvetica", "Helvetica-Bold"

    regular_path = next((p for p in FONT_CANDIDATES["regular"] if p.exists()), None)
    bold_path = next((p for p in FONT_CANDIDATES["bold"] if p.exists()), None)
    if not regular_path:
        return cid_fallback()
    try:
        regular_kwargs = {"subfontIndex": 0} if regular_path.suffix.lower() == ".ttc" else {}
        pdfmetrics.registerFont(TTFont("GuideSans", str(regular_path), **regular_kwargs))
        if bold_path:
            bold_kwargs = {"subfontIndex": 0} if bold_path.suffix.lower() == ".ttc" else {}
            pdfmetrics.registerFont(TTFont("GuideSansBold", str(bold_path), **bold_kwargs))
            return "GuideSans", "GuideSansBold"
        return "GuideSans", "GuideSans"
    except Exception as exc:  # pragma: no cover - platform-dependent font support
        print(f"Warning: Chinese font registration failed ({exc}); using built-in STSong-Light.")
        # Some Linux runners ship Noto CJK as PostScript-outline TTC files that
        # ReportLab cannot embed. Use the built-in CID fallback so CI PDFs
        # remain readable and text-extractable.
        return cid_fallback()


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullet_lines(items: Iterable[str], style: ParagraphStyle) -> list[Paragraph]:
    return [p(f"• {esc(item)}", style) for item in items]


def source_line(source: dict, body_style: ParagraphStyle, small_style: ParagraphStyle) -> list[Paragraph]:
    title = esc(source.get("title", "未命名来源"))
    grade = esc(source.get("grade", "C"))
    note = esc(source.get("note", ""))
    url = source.get("url") or ""
    if url.startswith(("https://", "http://")):
        link = f' <link href="{esc(url)}" color="#a93624">打开来源 ↗</link>'
    else:
        link = ""
    return [p(f"<b>[{grade}]</b> {title}{link}", body_style), p(note, small_style)]


def make_styles(font_regular: str, font_bold: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle("cover_kicker", parent=base["Normal"], fontName=font_bold, fontSize=9, leading=13, textColor=colors.HexColor("#a93624"), alignment=TA_CENTER, spaceAfter=15),
        "cover_title": ParagraphStyle("cover_title", parent=base["Title"], fontName=font_bold, fontSize=31, leading=39, textColor=colors.HexColor("#1d1d1b"), alignment=TA_CENTER, spaceAfter=14),
        "cover_sub": ParagraphStyle("cover_sub", parent=base["Normal"], fontName=font_regular, fontSize=12, leading=20, textColor=colors.HexColor("#62615c"), alignment=TA_CENTER),
        "cover_note": ParagraphStyle("cover_note", parent=base["Normal"], fontName=font_regular, fontSize=9, leading=15, textColor=colors.HexColor("#62615c"), alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=font_bold, fontSize=21, leading=27, textColor=colors.HexColor("#1d1d1b"), spaceBefore=4, spaceAfter=11, keepWithNext=True),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=font_bold, fontSize=14, leading=19, textColor=colors.HexColor("#1d1d1b"), spaceBefore=18, spaceAfter=7, keepWithNext=True),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=font_bold, fontSize=11.5, leading=16, textColor=colors.HexColor("#1d1d1b"), spaceBefore=12, spaceAfter=5, keepWithNext=True),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=font_regular, fontSize=9.3, leading=15, textColor=colors.HexColor("#2b2a27"), spaceAfter=5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=font_regular, fontSize=7.5, leading=11, textColor=colors.HexColor("#62615c"), spaceAfter=3),
        "label": ParagraphStyle("label", parent=base["BodyText"], fontName=font_bold, fontSize=7.5, leading=10, textColor=colors.HexColor("#a93624"), spaceBefore=8, spaceAfter=4),
        "toc": ParagraphStyle("toc", parent=base["BodyText"], fontName=font_regular, fontSize=10, leading=17, textColor=colors.HexColor("#2b2a27"), leftIndent=4, spaceAfter=4),
        "case_summary": ParagraphStyle("case_summary", parent=base["BodyText"], fontName=font_regular, fontSize=9.2, leading=15, textColor=colors.HexColor("#62615c"), spaceAfter=7),
        "quote": ParagraphStyle("quote", parent=base["BodyText"], fontName=font_regular, fontSize=9, leading=14, textColor=colors.HexColor("#a93624"), leftIndent=8, rightIndent=8, spaceBefore=5, spaceAfter=7),
    }


def header_footer(canvas, doc, font_regular: str, font_bold: str) -> None:
    canvas.saveState()
    width, height = doc.pagesize
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#d4cbbb"))
        canvas.setLineWidth(0.35)
        canvas.line(doc.leftMargin, height - 15 * mm, width - doc.rightMargin, height - 15 * mm)
        canvas.setFont(font_regular, 7.5)
        canvas.setFillColor(colors.HexColor("#77736b"))
        canvas.drawString(doc.leftMargin, height - 11.5 * mm, "低性价比人生指南 · 反面案例与高代价决策档案")
        canvas.drawRightString(width - doc.rightMargin, 11 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf(cases: list[dict], output: Path, page_size: tuple[float, float], label: str) -> None:
    font_regular, font_bold = register_fonts()
    styles = make_styles(font_regular, font_bold)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=page_size,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=22 * mm,
        bottomMargin=17 * mm,
        title="低性价比人生指南",
        author="qingchencloud",
        subject="错误建议与高代价决策反面案例库",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="guide", frames=[frame], onPage=lambda c, d: header_footer(c, d, font_regular, font_bold))])

    story: list = []
    story.extend([Spacer(1, 28 * mm), p("反面案例库 · 版本 0.2", styles["cover_kicker"]), p("低性价比<br/>人生指南", styles["cover_title"]), p("不是教你坑人，是教你识别坑。", styles["cover_sub"]), Spacer(1, 18 * mm)])
    cover_box = Table([[p("把那些看似聪明、便宜、效率高的建议拆开，记录它们如何变成金钱、时间、健康、关系和机会成本。<br/><br/><b>阅读顺序：</b>先看风险与止损，再看错误建议。指数只用于排序，不是科学测量。", styles["body"])]], colWidths=[doc.width * 0.78])
    cover_box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2c9bc")), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d84b2f")), ("LEFTPADDING", (0, 0), (-1, -1), 15), ("RIGHTPADDING", (0, 0), (-1, -1), 15), ("TOPPADDING", (0, 0), (-1, -1), 13), ("BOTTOMPADDING", (0, 0), (-1, -1), 13)]))
    story.extend([cover_box, Spacer(1, 24 * mm), p(f"{len(cases)} 条案例 · {len(set(c['category'] for c in cases))} 个场景 · {label}版", styles["cover_note"]), p("独立项目 · qingchencloud/low-cost-life-guide", styles["cover_note"]), PageBreak()])

    story.append(p("目录", styles["h1"]))
    story.append(p("本版由 data/cases.json 生成；网页与下载版共享同一份案例数据。", styles["small"]))
    grouped: dict[str, list[dict]] = {key: [] for key in CATEGORY_ORDER}
    for case in cases:
        grouped.setdefault(case["category"], []).append(case)
    for category in CATEGORY_ORDER:
        if not grouped.get(category):
            continue
        story.append(p(f"<b>{esc(category)}</b>　{len(grouped[category])} 条", styles["toc"]))
        story.append(p(esc(CATEGORY_INTROS.get(category, "")), styles["small"]))
    story.extend([Spacer(1, 9 * mm), p("证据等级：A 官方/系统综述　B 高质量研究　C 待核实或经验案例", styles["small"]), p("内容边界：高风险主题聚焦识别、后果、撤销和修复，不提供可直接复现的伤害或违法步骤。", styles["small"]), PageBreak()])

    for category in CATEGORY_ORDER:
        items = grouped.get(category, [])
        if not items:
            continue
        story.append(p(esc(category), styles["h1"]))
        story.append(p(esc(CATEGORY_INTROS.get(category, "")), styles["case_summary"]))
        story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#b9b0a2"), spaceBefore=2, spaceAfter=8))
        for case in items:
            story.append(p(f"{esc(case['id'])} · {esc(case['title'])}", styles["h2"]))
            story.append(p(esc(case["summary"]), styles["case_summary"]))
            meta = Table([[p(f"<b>指数 {case['score']['low_value_index']}</b>", styles["small"]), p(f"严重度：{esc(case['severity'])}", styles["small"]), p(f"证据：{esc(case['evidence_grade'])}", styles["small"]), p(f"更新：{esc(case['updated_at'])}", styles["small"])]], colWidths=[doc.width * 0.22, doc.width * 0.24, doc.width * 0.2, doc.width * 0.34])
            meta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eee8de")), ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#d4cbbb")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d4cbbb")), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            story.append(meta)
            story.append(p(esc(case["warning"]), styles["quote"]))
            story.append(p("场景", styles["label"]))
            story.append(p(esc(case["scenario"]), styles["body"]))
            story.append(p("为什么会被吸引", styles["label"]))
            story.append(p(esc(case["why_attractive"]), styles["body"]))
            story.append(p("隐藏成本", styles["label"]))
            cost_rows = []
            cost_labels = {"money": "钱", "time": "时间", "opportunity": "机会", "other": "其他"}
            for key, value in case.get("hidden_costs", {}).items():
                if value:
                    cost_rows.append([p(f"<b>{esc(cost_labels.get(key, key))}</b>", styles["small"]), p(esc(value), styles["small"])])
            if cost_rows:
                costs = Table(cost_rows, colWidths=[24 * mm, doc.width - 24 * mm])
                costs.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2c9bc")), ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#d4cbbb")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d4cbbb")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
                story.append(costs)
            story.append(p("失败机制", styles["label"]))
            story.extend(bullet_lines(case.get("failure_mechanism", []), styles["body"]))
            story.append(p("证据与来源", styles["label"]))
            for source in case.get("evidence", []):
                story.extend(source_line(source, styles["body"], styles["small"]))
            story.append(p("何时止损", styles["label"]))
            story.extend(bullet_lines(case.get("stop_loss", []), styles["body"]))
            story.append(p("更稳替代", styles["label"]))
            story.append(p(esc(case["safer_alternative"]), styles["body"]))
            story.append(p("决策前自检", styles["label"]))
            story.extend(bullet_lines(case.get("decision_checklist", []), styles["body"]))
            story.append(Spacer(1, 5 * mm))
            story.append(HRFlowable(width="100%", thickness=0.35, color=colors.HexColor("#d4cbbb"), spaceBefore=3, spaceAfter=8))
        story.append(PageBreak())

    story.append(p("方法与边界", styles["h1"]))
    story.append(p("低性价比指数 = 隐藏成本 + 风险严重度 + 不可逆性 − 表面收益。它用于编辑排序，不等于个人的医疗、法律或财务结论。A 级是官方或系统综述，B 级是高质量研究，C 级是待核实或经验案例。", styles["body"]))
    story.append(p("遇到紧急情况先使用当地正式求助渠道；健康、金融和法律内容需要结合所在地规则与最新来源判断。", styles["body"]))
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    cases = json.loads(DATA.read_text(encoding="utf-8"))
    out_dir = args.output_dir
    build_pdf(cases, out_dir / "low-cost-life-guide.pdf", A4, "A4")
    build_pdf(cases, out_dir / "low-cost-life-guide-a5.pdf", A5, "A5")
    print(f"Built {out_dir / 'low-cost-life-guide.pdf'}")
    print(f"Built {out_dir / 'low-cost-life-guide-a5.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
