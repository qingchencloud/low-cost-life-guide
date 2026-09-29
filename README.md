# 低性价比人生指南

> **不是教你坑人，是教你识别坑。**
>
> 错误建议与高代价决策的反面案例库：把“看起来省一点、快一点、聪明一点”的选择，拆成诱因、隐藏成本、失败机制和止损路径。

这是一个独立项目，灵感来自 [HowToLiveBetter / 高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter) 的内容工程方式，但不代表其官方镜像、分支或附属项目。原项目已经有“反面清单”；本项目把重点放在跨场景的失败决策复盘：消费、工作、关系、隐私、健康和创业。

## 在线阅读

- GitHub Pages：<https://qingchencloud.github.io/low-cost-life-guide/>
- A4 PDF：[`downloads/low-cost-life-guide.pdf`](downloads/low-cost-life-guide.pdf)
- A5 / 手机 PDF：[`downloads/low-cost-life-guide-a5.pdf`](downloads/low-cost-life-guide-a5.pdf)
- 本地预览：`python -m http.server 4173`，打开 <http://localhost:4173>
- 手机安装：用移动浏览器打开在线版，通过“添加到主屏幕”安装 PWA；首次打开后可在弱网下继续查看已缓存内容。

## 现在有什么

- 24 条可检索反面案例，覆盖 7 个场景和 7 类损失
- 全文搜索、场景/风险/证据/严重度筛选
- 低性价比指数、证据等级和更新时间
- 案例详情抽屉：表面收益 → 隐藏成本 → 失败机制 → 证据 → 止损 → 稳妥替代
- URL 查询参数和 `#case=slug` 深链，可直接分享筛选结果或案例
- 纯静态 HTML/CSS/JavaScript，无后端、无运行时依赖
- A4 打印版和 A5 移动阅读版 PDF，使用同一份 JSON 数据生成
- PWA manifest + Service Worker，支持添加到主屏幕和弱网缓存
- GitHub Pages 工作流和数据校验脚本

## 快速开始

```powershell
git clone https://github.com/qingchencloud/low-cost-life-guide.git
cd low-cost-life-guide
python -m http.server 4173
```

访问 <http://localhost:4173>。直接双击 `index.html` 时，浏览器会阻止 `fetch(data/cases.json)`，请使用本地 HTTP 服务。

验证数据：

```powershell
python scripts/validate.py
# 或
npm run validate
```

生成 PDF（需要 `pip install -r requirements-pdf.txt`）：

```powershell
python scripts/build_pdf.py
```

构建脚本会生成 `downloads/low-cost-life-guide.pdf`（A4）和 `downloads/low-cost-life-guide-a5.pdf`（A5 / 手机阅读）。

## 目录

```text
低性价比人生指南/
├─ index.html                 # 静态入口和信息架构
├─ styles.css                # 编辑型、纸张感视觉系统
├─ app.js                    # 搜索、筛选、排序、详情抽屉
├─ manifest.webmanifest      # PWA 安装信息
├─ sw.js                     # 弱网缓存与更新策略
├─ assets/icon.svg           # PWA 矢量图标
├─ assets/icon-192.png       # PWA 安装图标
├─ assets/icon-512.png       # PWA 安装图标
├─ downloads/                # A4 / A5 PDF 阅读版
├─ data/cases.json           # 案例单一数据源
├─ data/taxonomy.json        # 分类、章节与风险标签
├─ book/                     # 按章节阅读的 Markdown 文本
├─ docs/methodology.md       # 指数、证据和编辑方法
├─ docs/contribute.md        # 提交流程和审核清单
├─ templates/case.md         # 新案例模板
├─ scripts/validate.py       # 无依赖数据校验
├─ scripts/build_pdf.py      # 从 JSON 生成 A4/A5 PDF
├─ requirements-pdf.txt      # PDF 构建依赖
└─ .github/workflows/pages.yml
```

## 案例格式

每条案例都要把“错误建议”与“修复路径”放在同一张卡片里：

1. **反面建议**：清楚标为分析材料，默认折叠。
2. **场景与诱因**：它为什么看起来合理，前提漏在哪里。
3. **实际代价**：钱、时间、机会、健康、隐私、法律或声誉。
4. **失败机制**：解释决策如何一步步滑向高成本结果。
5. **证据**：A 为官方/系统综述，B 为高质量研究，C 为待核实或经验案例。
6. **止损**：给出触发条件、停止动作、证据保留和求助路径。
7. **稳妥替代**：提供同一目标的低风险选择。

## 低性价比指数

页面中的指数是透明的编辑排序工具，不是科学测量：

```text
低性价比指数 = 隐藏成本 + 风险严重度 + 不可逆性 - 表面收益
```

原始字段保存在 `data/cases.json`：

- `apparent_gain`：当下看起来得到的收益，0—5
- `cost`：综合隐藏成本，0—5
- `irreversibility_penalty`：回头难度，0—3
- `low_value_index`：0—100 的展示排序值

不同案例不跨维度做精确比较；指数高只表示“更值得先读止损部分”。

## 编辑边界

- 高风险主题集中在识别信号、后果、撤销和修复，不写可直接复现的伤害或违法操作参数。
- 健康、金融和法律条目优先使用官方文件、原始研究或系统综述，并标注最后核实时间。
- 真实人物、公司和金额做匿名化或泛化；事实、推断和个人经验分栏。
- 案例不是医疗、法律、财务或心理诊断意见；遇到紧急情况先使用当地正式求助渠道。

## 贡献

打开 [`docs/contribute.md`](docs/contribute.md)，复制 [`templates/case.md`](templates/case.md)，提交一个可匿名、可复盘、带来源或明确标注经验性质的案例。大型改动先开 Issue，避免重复选题。

## 许可证

- 代码：MIT，见 [`LICENSE`](LICENSE)
- 案例正文与编辑内容：CC BY 4.0，见 [`CONTENT-LICENSE.md`](CONTENT-LICENSE.md)

欢迎引用本项目，但不要把独立项目描述成 HowToLiveBetter 官方版本。
