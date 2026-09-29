#!/usr/bin/env python3
"""Generate chapter Markdown from the canonical JSON dataset."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data/cases.json").read_text(encoding="utf-8"))
ORDER = ["消费与财务", "职场与学习", "工具与效率", "信息与隐私", "健康误区", "低效决策", "关系与沟通"]
SLUGS = {
    "消费与财务": "01-消费与财务",
    "职场与学习": "02-职场与学习",
    "工具与效率": "03-工具与效率",
    "信息与隐私": "04-信息与隐私",
    "健康误区": "05-健康误区",
    "低效决策": "06-低效决策",
    "关系与沟通": "07-关系与沟通",
}
INTRO = {
    "消费与财务": "把价格、收入和现金流放回同一张账里，识别“便宜”背后的锁定成本。",
    "职场与学习": "把忙碌、证书和在线时长还原成可验收的结果与机会成本。",
    "工具与效率": "工具服务于任务；当配置、迁移和追新成为任务本身，就该停下来复盘。",
    "信息与隐私": "传播速度不等于证据强度，公开范围也不等于可控范围。",
    "健康误区": "先识别风险和求助边界，再谈习惯、效率和自我管理。",
    "低效决策": "把后悔拆成变量，用小实验、退出条件和可迁移资产减少重复下注。",
    "关系与沟通": "边界是自己的行动，沟通是可验证的约定，不靠制造压力测试关系。",
}


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_case(item: dict) -> str:
    costs = item.get("hidden_costs", {})
    cost_lines = []
    labels = {"money": "钱", "time": "时间", "opportunity": "机会", "other": "其他"}
    for key, value in costs.items():
        if value:
            cost_lines.append(f"- **{labels.get(key, key)}**：{value}")
    evidence_lines = []
    for source in item.get("evidence", []):
        link = f" [{source.get('url')}]({source['url']})" if source.get("url") else "（匿名复盘或待核实材料）"
        evidence_lines.append(f"- **{source.get('grade', 'C')}** {source.get('title', '未命名来源')}{link}：{source.get('note', '')}")
    return f'''## {item["id"]} · {item["title"]}

> **反面示例｜请先看风险与止损。** {item["warning"]}

- 低性价比指数：**{item["score"]["low_value_index"]} / 100**
- 严重度：**{item["severity"]}**
- 证据等级：**{item["evidence_grade"]}**
- 最后更新：**{item["updated_at"]}**

### 反面建议（分析材料）

> {item["wrong_advice"]}

### 场景

{item["scenario"]}

### 为什么会被吸引

{item["why_attractive"]}

### 隐藏成本

{chr(10).join(cost_lines)}

### 失败机制

{bullets(item["failure_mechanism"])}

### 证据与来源

{chr(10).join(evidence_lines)}

### 何时止损

{bullets(item["stop_loss"])}

### 更稳替代

{item["safer_alternative"]}

### 决策前自检

{bullets(item["decision_checklist"])}

'''


def main() -> int:
    book = ROOT / "book"
    book.mkdir(exist_ok=True)
    grouped = {category: [] for category in ORDER}
    for item in CASES:
        grouped.setdefault(item["category"], []).append(item)
    index = ["# 目录", "", "> 本目录由 `data/cases.json` 生成。网页、PDF 与章节阅读版共享同一份案例数据。", ""]
    chapter_number = 0
    for category in ORDER:
        if not grouped.get(category):
            continue
        chapter_number += 1
        slug = SLUGS[category]
        index.append(f"{chapter_number}. [{category}]({slug}.md) · {len(grouped[category])} 条")
        index.append("")
        content = [f"# {slug}", "", f"> {INTRO[category]}", "", "> 先看风险与止损，再看错误建议；指数只用于编辑排序。", ""]
        for item in grouped[category]:
            content.append(render_case(item))
        (book / f"{slug}.md").write_text("\n".join(content).rstrip() + "\n", encoding="utf-8")
    (book / "README.md").write_text("\n".join(index).rstrip() + "\n", encoding="utf-8")
    print(f"Generated {sum(bool(items) for items in grouped.values())} chapters and {len(CASES)} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())