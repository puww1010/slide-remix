"""Example: phase pipeline (N phases x M steps + loop + capability cards + closing banner).
Illustrative content (generic agent-harness execution flow).
Added text (not in source, report on delivery): the status pill."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from spec_lib import *

TITLE_BOX = (58, 38, 940, 32)
SUBTITLE_TOP = 84

TITLE = 'Agent 执行一次任务的 13 个步骤'
SUBTITLE = '模型负责推理，Harness 负责把推理变成受控、可验证的执行'

PHASES = [  # (title, colour, steps[(title lines, desc lines)])
    ('1. 任务接入与上下文装配', C('blue'), [
        (['用户下达任务'], ['通过 Web、IDE', '或 API 提交', '任务需求']),
        (['装配上下文'], ['构建模型需要', '的上下文信息', '（Prompt、', '工具、历史等）']),
        (['预算闸门', '与压缩'], ['控制 Token', '预算，压缩', '历史信息，', '保留关键状态'])]),
    ('2. 模型推理与工具调用', C('green'), [
        (['发起模型', '调用'], ['发送请求给', 'LLM']),
        (['模型输出'], ['返回文本或', '工具调用请求'])]),
    ('3. 安全控制与执行保障', C('orange'), [
        (['解析与参数', '校验'], ['检查工具名称、', '参数格式等']),
        (['权限准入', '网关'], ['基于身份和策略', '进行权限判断']),
        (['人工确认'], ['高风险操作', '需人工审批'])]),
    ('4. 工具执行与结果回写', C('purple'), [
        (['在受控工作', '区执行'], ['运行工具，', '受控环境执行']),
        (['连接真实', '系统'], ['访问数据库、', 'API、MCP 等', '外部系统'])]),
    ('5. 执行闭环与最终交付', C('teal'), [
        (['结果规范化', '并回注'], ['处理工具结果，', '回写上下文']),
        (['出口判定'], ['判断任务是否', '完成，决定', '继续、重试', '或结束']),
        (['定稿并交付'], ['输出最终结果', '（文件、', '报告等）'])]),
]
ARCH = [('LLM', '理解与推理', C('green', 'dark')), ('Context', '任务上下文', C('purple')),
        ('Tools', '外部能力', C('blue')), ('Harness', '执行控制与安全', C('orange'))]
CAPS = [('上下文工程', '（Context Engineering）', ['上下文组装、压缩与管理', '让模型知道什么']),
        ('工具编排', '（Tool Orchestration）', ['工具注册、调度与调用', '让模型用好工具']),
        ('权限与安全', '（Permission & Security）', ['身份认证、权限控制、沙箱隔离', '让 Agent 安全可控']),
        ('执行循环', '（Execution Loop）', ['状态管理、重试与终止', '让任务有始有终']),
        ('可观测与审计', '（Observability）', ['Trace、日志与审计', '让过程可追溯'])]

X0, X1 = 24, 1256

def build_spec():
    P = []
    P.append(T(57, 84, 900, [line1(SUBTITLE, 13, C('muted'))], name='Subtitle'))
    # status pill
    P += [R(1000, 34, 240, 44, fill=C('green', 'bg'), stroke=C('green'), sw=1.5, rx=22, name='Status pill'),
          CHK(1025, 56, name='Status check'),
          T(1043, 38, 195, [line1('13 个关键步骤 · 5 个执行阶段', 13, C('green', 'dark'), True, 18),
                            line1('Harness 五项核心工程能力', 10.5, C('green', 'dark'), False, 14)], name='Status text')]

    # ---- Agent architecture band ----
    by, bh = 106, 54
    P += [R(X0, by, X1 - X0, bh, fill=C('zone'), stroke=C('line'), rx=10, name='Zone architecture'),
          T(X0 + 16, by + 18, 120, [line1('Agent 整体架构', 13, C('ink'), True)], name='Architecture label')]
    nx0, gap = 160, 30
    nw = (X1 - 10 - nx0 - 3 * gap) / 4
    for k, (t, s, c) in enumerate(ARCH):
        x = nx0 + k * (nw + gap)
        emph = c == C('orange')
        P.append(R(x, by + 7, nw, bh - 14, fill=C('white'), stroke=c, sw=2.0 if emph else 1.6, rx=7, name=f'Arch {t}'))
        P.append(T(x, by + 12, nw, [line1(t, 13, C('ink'), True, 17), line1(s, 10.5, C('soft'), False, 14)],
                   align='c', name=f'Arch {t} text'))
        if k < 3:
            P.append(T(x + nw, by + 15, gap, [line1('+', 18, C('soft'), True, 22)], align='c', name='Plus'))

    # ---- 5 phases x 13 steps ----
    zy, zh = 178, 194
    ZG, PAD, G = 6, 5, 10
    nwid = (X1 - X0 - 4 * ZG - 10 * PAD - 8 * G) / 13
    ny, nh = 208, 156
    x = X0
    step = 0
    centers = []
    for pi, (pt, c, steps) in enumerate(PHASES):
        zw = 2 * PAD + len(steps) * nwid + (len(steps) - 1) * G
        P.append(R(x, zy, zw, zh, fill=C(c[0], 'fill'), stroke=C(c[0], 'border'), sw=1.0, rx=10, name=f'Phase {pi+1}'))
        P.append(T(x + 10, zy + 8, zw - 16, [line1(pt, 12.5, c, True)], name=f'Phase {pi+1} title'))
        for si, (tl, dl) in enumerate(steps):
            step += 1
            nx = x + PAD + si * (nwid + G)
            centers.append(nx + nwid / 2)
            P.append(R(nx, ny, nwid, nh, fill=C('white'), stroke=c, sw=1.4, rx=7, name=f'Step {step}'))
            P.append(NUM(step, nx + 14, ny + 15, c))
            P.append(T(nx + 1, ny + 32, nwid - 2, [line1(t, 12, C('ink'), True, 16) for t in tl], align='c', name=f'Step {step} title'))
            P.append(T(nx + 1, ny + 76, nwid - 2, [line1(d, 10, C('muted'), False, 14.5) for d in dl], align='c', name=f'Step {step} text'))
            if step < 13:
                last = si == len(steps) - 1
                gx = nx + nwid + ((PAD + ZG + PAD) if last else G) / 2
                P.append(TRI(gx, ny + nh / 2, c, 4.5, name=f'Arrow {step}'))
        x += zw + ZG

    # ---- execution loop ----
    ly = 400
    P.append(PL([(centers[-1], ny + nh + 2), (centers[-1], ly), (centers[0], ly), (centers[0], ny + nh + 4)], C('blue'), 2.0,
                tail=True, name='Execution loop'))
    P += [R(640 - 100, ly - 12, 200, 24, fill=C('white'), stroke=C('blue'), sw=1.5, rx=12, name='Loop pill'),
          T(540, ly - 8, 200, [line1('Agent Execution Loop', 12, C('blue'), True, 16)], align='c', name='Loop pill text'),
          T(340, ly + 18, 600, [line1('根据任务状态，持续推理、执行和验证', 11, C('muted'))], align='c', name='Loop caption')]

    # ---- five capabilities ----
    cy, ch = 450, 114
    P += [R(X0, cy, 128, ch, fill=C('zone'), stroke=C('line'), rx=8, name='Capabilities label box'),
          T(X0 + 14, cy + 28, 110, [line1('Harness 的', 14, C('ink'), True, 20), line1('五项核心', 14, C('ink'), True, 20),
                                    line1('工程能力', 14, C('ink'), True, 20)], name='Capabilities label')]
    cx0, cg = X0 + 140, 12
    cw = (X1 - cx0 - 4 * cg) / 5
    for k, (t, en, bl) in enumerate(CAPS):
        x = cx0 + k * (cw + cg)
        P += [R(x, cy, cw, ch, fill=C('white'), stroke=C('line'), rx=6, name=f'Capability {k+1}'),
              R(x, cy, cw, 4, fill=C('green'), rx=0, name=f'Capability {k+1} bar'),
              CHK(x + 22, cy + 30, name=f'Capability {k+1} check'),
              NUM(k + 1, x + cw - 20, cy + 26, C('orange')),
              T(x + 40, cy + 21, cw - 70, [line1(t, 13.5, C('ink'), True, 18)], name=f'Capability {k+1} title'),
              T(x + 40, cy + 41, cw - 46, [line1(en, 10.5, C('soft'), False, 14)], name=f'Capability {k+1} en'),
              T(x + 22, cy + 66, cw - 30, [line1(b, 11.5, C('muted'), False, 19) for b in bl], name=f'Capability {k+1} text')]

    # ---- closing banner ----
    P += [R(X0, 588, X1 - X0, 44, fill=C('orange', 'fill'), rx=6, name='Banner'),
          R(X0, 588, 5, 44, fill=C('orange'), rx=0, name='Banner bar'),
          T(X0, 599, X1 - X0, [([('任务是否完成，', C('ink'), True), ('由 Harness 的出口判定决定', C('orange'), True),
                                 ('，而不是模型的一句“做完了”', C('ink'), True)], 15, 20)], align='c', name='Banner text')]
    return P
