---
name: slide-remix
metadata:
  version: "1.1"
description: 拆解 slide 截图（用什么做的、要准备哪些素材、怎么复刻），以及把公众号图、截图或零散笔记重绘成统一的扁平风 16:9 架构图（HTML + PNG），并用同一份布局套任意 .pptx 模版出可编辑 PPTX。当用户说"分析这个 slide 是用什么做的 / 拆解这张图 / 做一个类似的 / 按 A 路线做 / 把这张图做成 html 和 pptx / 套这个模版转成 pptx / 同样的逻辑再做一张"时使用。
---

# slide-remix

一份布局定义（`spec.py`，1280×720 px）同时生成两种产物：**HTML/PNG**（固定的扁平视觉规范）和 **PPTX**（任意模版，原生形状，模版配色）。两者的位置和文字完全一致，唯一的差异是配色映射（以及随配色改动的图例颜色词）。

## 三种模式

| 模式 | 什么时候用 | 产出 |
|---|---|---|
| A 拆解分析 | "这个 slide 用什么做的 / 用了什么 skill / 要什么素材 / 怎么做类似的" | 对话里的中文分析，不出文件 |
| B 重绘成扁平风 | "按这个风格做一个 / 做成 html" | `<名>.html` + `<名>.png` |
| C 套模版出 PPTX | "用这个模版转成 pptx / 也要 pptx" | `<前缀>_<主题>.pptx` + 预览图 |

只想把一张截图原样转成可编辑 PPT、不改风格的，用 `image-to-editable-ppt`；想把已有页面原样套进公司模版、按原图清理对齐的，用 `screenshot-to-template-slide`。这两种情况都不用本 skill。

## 第 0 步：运行前检查（每次都做）
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/doctor.py --need html,png,pptx,preview [--template T.pptx]
```
- 按 `[summary]` 告诉用户这台机器能做哪些产物：例如 "PNG 截图做不了（缺浏览器），HTML 和 PPTX 可以"。缺的工具照 `fix:` 行给出安装办法；`--fix` 会尝试自动安装不需要 root 的部分（playwright、Chromium、Linux 系统库）。
- `--need` 只写用户这次要的产物。退出码 1 表示要的产物里有做不了的，先和用户确认是改做其他产物，还是先装工具。
- 没有用户模版、只想试一下 PPTX 效果时，加 `--template demo`，用自带的虚构品牌示例模版（以 base64 文本存放在 `examples/demo-template.pptx.b64`，脚本首次使用时自动解码到临时目录）。

## 开场：一次问清楚（用 AskUserQuestion）
1. **要哪些产物**：只要 HTML/PNG，还是同时要 PPTX？要 PPTX 就确认模版文件。
2. **中文字体**（页面有中文、且要 PPTX 时**每次都问**，不设默认）：
   - `PingFang SC`：Mac 上效果最好，在 Windows 上会被替换；
   - `Microsoft YaHei`：Windows 自带，发给别人或放映时最稳。
3. **原图水印**：默认去掉；需要标注来源时，在脚注写"内容参考：…"。
4. **视觉风格**：默认用 `references/design-system.md` 里的扁平规范。用户另给了参考图时，先拆解那张图（模式 A），再把它的视觉要素更新进这次的 spec。

## 硬规则
- **文字**：原图文字逐字保留，只允许重新断行；凡是补的字（状态胶囊、卡片说明、替换原图乱码编号的连线标签等），交付时逐条列出，请用户确认。
- **结构**：保持原图的分区、顺序和相对位置。竖版改横版时可以重排，但要说明怎么排的。
- **颜色**：spec 里只写语义色 `C('orange')` 这种形式，不写 hex。图例里的颜色词必须用 `cw('orange')`，套模版后会自动变成实际的颜色词（比如模版里没有紫色，"紫色"会自动变成"青色"）。
- **图标极简**：只给主体（人 / Agent / 团队成员）配图标，用 `ICON()`，两种产物里是同一套原生形状图标。
- **PPTX**：只改本页 slide 和它的 rels，不动模版里的其他文件；颜色只用 scheme color。
- **隐私**：页面上有真实姓名或组织架构时，交付时提醒仅限内部使用。示例里一律用虚构人名。

## 模式 A：拆解分析
按 `references/analysis-checklist.md` 来做：
1. 先放大局部找证据：外框、页脚 / logo、字体、跳线、标签底色、图标风格、对齐精度、文案口吻；
2. 输出结构固定为："结论 + 把握程度 → 证据 → 设计语法（可抄的规则 + 可改进处）→ 需要的素材 → 复刻路线（落到具体 skill）"；
3. 判断不了的就直说判断不了，不要编工具名。

## 模式 B / C：工作流（每步都有验证点）
1. **抄文字清单**：把原图文字逐条写进 `source_text.txt`，一行一条，以 `#` 开头的行是注释。这是最后核对的基准。
2. **选页型**：在 `references/layout-patterns.md` 里找最接近的页型，复制对应的 `examples/*.py` 作为起点。
3. **写 spec**：坐标单位是 px（画布 1280×720）。API 见下文。在文件开头的 docstring 里记下来源和补了哪些字。
4. **出 HTML + PNG 并自检**：
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/make_html.py --spec page.py --out OUT.html --png OUT.png --source source_text.txt
   ```
   文字清单的写法见 `examples/simple_steps.source.txt`。
   用 Read 打开 PNG，按 `references/lessons.md` 的清单检查：重叠、溢出、标签被线切开、贴边、留白。`[text check] missing` 必须是 none，`added` 列出的就是要向用户报告的补充文字。
5. **出 PPTX**（模式 C）：
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/make_pptx.py --spec page.py --template T.pptx --out OUT.pptx \
       --qa-dir <能用 Read 打开的目录>/QA --ea-font "<用户选的字体>" --source source_text.txt
   ```
   脚本会自动完成以下几步：
   - 探测模版：画布尺寸、色相配色映射、版式（优先 Title Only light，同品牌系列优先）、标题占位符、页脚 / logo 的安全区；
   - 调标题：标题太长时在本页调小字号，标题区压到副标题时把标题挪到 `TITLE_BOX`；
   - 构建：validate、和模版逐文件比对、lint、字号放大 6% 的压力渲染；
   - 文字核对。

   看压力渲染图，确认这几项都通过：`[validate] PASSED`、`[diff]` 只改了 slide1 和它的 rels、`[lint] OK`、`[safe area] OK`、`[text check] none`。
6. **交付**：把文件复制到用户的文件夹，用 present_files 给出。汇报要简短，必须写清：
   - 补了哪些字；
   - 配色替换（`[colors]` 行）和图例颜色词的变化；
   - 标题字号或位置有没有在本页调整（`[title]` 行）；
   - 字体提醒（`[NOTE] font`）；
   - 预览图是 LibreOffice 渲染的，请用户在 PowerPoint 里再看一遍。

## 常见失败与处理
所有脚本只用三种退出码：0 成功（但要读 `[WARN]` 行）、1 `[FAIL]` 不能交付、2 只用于 make_html，表示 HTML 已生成、PNG 截图失败。

| 输出 | 意思 | 怎么做 / 怎么告诉用户 |
|---|---|---|
| `[FAIL] spec … raised … unknown colour role / ICON kind` | spec 写错 | 按提示改 spec 里那一行，重跑 |
| `[FAIL] spec file not found` / `must define TITLE and build_spec()` | 路径或结构不对 | 修正路径；照 examples 补齐 TITLE 和 build_spec |
| `[FAIL] template not found` / `is not a .pptx` | 模版路径错或格式不对 | 请用户提供 .pptx（.potx / Keynote / PDF 先另存为 .pptx） |
| `[FAIL] layout … not found` / `no Title Only / Blank layout` | 自动选不到版式 | 用 `--layout "<版式名>"` 指定，版式名在 probe.json 的 `layouts` 里 |
| `[FAIL] validate: …` | 生成的文件没通过校验 | 不要交付；重跑 doctor，换模版或把报错发给维护者 |
| `[png] FAILED: …`（退出码 2） | 截图环境缺东西（浏览器、系统库、离线） | HTML 照常交付，告诉用户 PNG 没做成及原因；可以 `doctor.py --fix` 后重跑，或请用户在浏览器里打开 HTML 自己截图 |
| `[WARN] no preview render: …` | 没装 LibreOffice / pdftoppm，PPTX 已生成但没做视觉检查 | 交付时明确说"这页没做渲染检查，请在 PowerPoint 里看一遍"，并给出安装办法 |
| `[WARN] footer safe-area detection skipped` | 测不了模版页脚位置，按 680px 估 | 内容尽量放在 y≈650 以上；交付时提醒检查页脚是否被遮挡 |
| `[WARN] roles … all map to …` | 两个语义色在这个模版里成了同一种颜色 | 用 `--color ROLE=accentN` 指定，或靠图标、文字区分 |
| `[validate:basic] PASSED (pre-existing template findings ignored)` | 没有 Anthropic pptx skill，用了内置的基本校验；模版本身的问题不算 | 可以交付；需要更严格的校验时装 pptx skill |

## spec API（`scripts/spec_lib.py`）
spec 文件放在任何目录都可以，直接写 `from spec_lib import *` 即可，两个脚本会自动把 `scripts/` 加进 sys.path。
```python
from spec_lib import *
TITLE = '页面标题'                # 由渲染器绘制：HTML 画标题和橙色竖条，PPTX 放进模版的标题占位符
TITLE_BOX = (58, 38, 940, 32)   # 标题可占的区域；右边缘是避让线（右上角放胶囊时把 w 缩到胶囊左边为止）
SUBTITLE_TOP = 84               # 标题下方第一个元素的 top；没有副标题时填第一个元素的 y
TITLE_SIZE = 24                 # 可选，HTML 标题字号（px）
HTML_DY = 0                     # 可选，HTML 整体下移量；不写时自动计算（最多 18px）
def build_spec():
    return [T(57, 84, 900, [line1('副标题', 13, C('muted'))], name='Subtitle'), ...]   # 副标题要自己画
```
| 元素 | 用途 |
|---|---|
| `R(x,y,w,h, fill, stroke, sw=1, rx=8, dash=None, name)` | 矩形 / 圆角矩形 / 分区框；`dash='dash'\|'dot'`；`rx<=1` 时是直角 |
| `T(x,y,w, lines, align='l'\|'c', name)` | 文本，y 是第一行的顶边。`lines=[line1(text, size, color, bold=False, lh=size×1.35)]`；一行多种样式时写成 `([(t,color,bold),...], size, lh)` |
| `PL(pts, color, sw=2, head=False, tail=False, dash=None, name)` | 折线连线，`head` / `tail` 加箭头 |
| `TRI(cx,cy,color,s=5,name)` | 很窄的间隙里用的小三角箭头 |
| `NUM(n,cx,cy,color,r=9,size=10.5)` / `CHK(cx,cy,r=10,name)` | 编号圆 / 绿色勾选圆 |
| `ICON(kind,cx,cy,s,color,name)` | 原生图标：person people globe cloud shield_ok chip building test deploy terminal search clock chat book target |
| `LABEL(t,x,y_base,size,color,anchor='m'\|'s'\|'e')` | 连线上的标签（自带白底），返回一个列表，用 `P += LABEL(...)`；最后添加，保证在线的上层 |
| `BULLETS(x,y,w,items,size,color,lh,gap,name)` | 要点列表，断行由 `wrap()` 决定，HTML 和 PPTX 一致 |

`name=` 会成为 PPTX 里的形状名，建议写上，方便用户在"选择窗格"里找到对应的形状。

## 产物命名和附带文件
- PPTX 命名为 `<模版品牌简称>_<主题>.pptx`，例如 `ACME_Agent_Harness.pptx`；HTML/PNG 用主题的英文短名。
- `make_pptx.py` 会在输出旁边写一个 `OUT.probe.json`（模版探测结果的缓存）；换模版或换版式时会自动重新探测，也可以加 `--reprobe` 强制刷新。这个文件不需要交给用户。
- `[title]` 行写的是"no change"时，说明标题直接继承了模版的标题占位符。
- `[layout]` 行是自动选中的版式。不合适时用 `--layout "<版式名>"` 指定，可选的版式名列在 probe.json 的 `layouts` 里。
- 对配色映射不满意时（例如核心的 orange 被映射成了黄色），加 `--color orange=accent6` 手动指定（可以写多个）；图例颜色词会自动跟着改。脚本发现两个语义色映射成了同一个颜色词时，会打印 `[WARN]`。

颜色写法：`C(role, variant)`。
- `role`：`orange` 执法/安全/请求入口，`blue` 调用/数据，`purple` 身份/上下文，`green` 通过/状态，`teal`，`gray`；中性色 `ink` `muted` `soft` `white` `line` `zone`。
- `variant`：`base`、`fill`（约 7% 浅色底）、`bg`（约 10%）、`border`（约 40%）、`dark`（加深 50%）。

## 文件
- `scripts/doctor.py`：运行前检查，列出每项工具影响哪种产物、怎么安装（macOS / Debian-Ubuntu）。
- `scripts/make_html.py`：spec → HTML + PNG。截图依赖 playwright；playwright、chromium、缺失的系统库会自动补装（用 `apt-get download` 下载后本地解压，不需要 root），整个截图过程限时 120 秒，离线时会立即说明原因，不会卡住；`--no-install` 可关闭自动安装。
- `scripts/crop.py`：模式 A 用的局部放大工具，`--box x0,y0,x1,y1 --scale 3` 放大一块，`--grid 3x3` 切成小图。
- `scripts/make_pptx.py`：spec + 任意模版 → PPTX，含探测和 QA。
- `scripts/template_probe.py`：可单独运行，查看一个模版的配色映射、版式、标题和安全区。
- `scripts/render_svg.py` / `scripts/to_pptx.py`：两个渲染器。
- `scripts/vendor/`：`slidekit.py`、`build_slide.py`、`list_layouts.py`，来自 screenshot-to-template-slide（MIT，见 LICENSE 文件）。
- `examples/`：`harness_arch.py`（三栏架构）、`steps_pipeline.py`（阶段流水线）、`simple_steps.py`（简单 N 步流程，附 `simple_steps.source.txt` 文字清单示例）、`team_grid.py`（卡片网格）；`demo-template.pptx.b64` 是虚构品牌 ACME 的示例模版（`--template demo` 使用）。
- `tests/run_examples.sh OUT_DIR [T.pptx …]`：先跑 doctor，再把所有示例生成 HTML/PNG 和 PPTX；不给模版时用 `demo`。
- `references/`：`design-system.md`、`layout-patterns.md`、`analysis-checklist.md`、`lessons.md`。
