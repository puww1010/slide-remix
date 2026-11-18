"""Example: three-zone architecture (users | execution zone (dashed) | external dependencies)
+ bottom cards + legend footnote. Illustrative content (generic agent-harness architecture).
Added text (report on delivery): status pill, bottom-card descriptions, connector labels replacing the source's M1–M9 codes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from spec_lib import *

TITLE = 'Agent Harness 架构图'
TITLE_BOX = (58, 38, 940, 32)
SUBTITLE_TOP = 84

CTX, ORG, BLU, GRY, DSH = C('purple'), C('orange'), C('blue'), C('gray'), C('soft', 'border')

def node(name, x, y, w, h, title, sub, color, sw=1.6, fill=None, n=None):
    P = [R(x, y, w, h, fill=fill or C('white'), stroke=color, sw=sw, rx=8, name=name),
         T(x, y + h / 2 - 17, w, [line1(title, 13.5, C('ink'), True, 19), line1(sub, 10.5, C('soft'), False, 15)],
           align='c', name=name + ' text')]
    if n: P.append(NUM(n, x + 13, y + 13, C('green'), r=8, size=9.5))
    return P

def zone(name, x, y, w, h, fill, stroke, label, lc=C('soft'), dash=None):
    return [R(x, y, w, h, fill=fill, stroke=stroke, sw=1.2, rx=10, dash=dash, name=name),
            T(x + 14, y + 12, w - 28, [line1(label, 10.5, lc, True, 15)], name=name + ' label')]

def build_spec():
    P = [T(57, 84, 900, [line1('会话、编排、策略、工具、安全与运行时如何协同工作', 13, C('muted'))], name='Subtitle'),
         R(1000, 34, 240, 44, fill=C('green', 'bg'), stroke=C('green'), sw=1.5, rx=22, name='Status pill'),
         CHK(1025, 56, name='Status check'),
         T(1043, 38, 195, [line1('8 个核心模块 · 5 类外部依赖', 13, C('green', 'dark'), True, 18),
                           line1('Agent 工程底座 · 统一可观测', 10.5, C('green', 'dark'), False, 14)], name='Status text')]
    P += zone('Zone users', 40, 110, 160, 380, C('zone'), C('line'), '用户 / 客户端')
    P += zone('Zone harness', 215, 110, 690, 380, C('orange', 'fill'), C('orange', 'border'), 'AGENT HARNESS · 工程底座',
              lc=ORG, dash='dash')
    P += zone('Zone external', 920, 110, 320, 380, C('blue', 'fill'), C('blue', 'border'), '外部依赖')

    # connectors first (nodes are drawn on top)
    P += [PL([(188, 285), (238, 285)], ORG, tail=True, name='Flow user to 2'),
          PL([(330, 214), (330, 250)], CTX, 1.8, head=True, tail=True, name='Flow 1-2'),
          PL([(422, 180), (468, 180)], CTX, 1.8, head=True, tail=True, name='Flow 1-5'),
          PL([(422, 270), (555, 270), (555, 214)], CTX, 1.8, head=True, tail=True, name='Flow 2-5'),
          PL([(422, 298), (745, 298), (745, 214)], CTX, 1.8, tail=True, dash='dash', name='Flow 2-4'),
          PL([(815, 350), (815, 214)], BLU, tail=True, name='Flow 7-4'),
          PL([(330, 318), (330, 350)], BLU, tail=True, name='Flow 2-3'),
          PL([(688, 384), (642, 384)], ORG, tail=True, name='Flow 7-6')]
    P += [PL([(x, 418), (x, 438)], DSH, 1.6, tail=True, dash='dot', name='Collect') for x in (330, 555, 785)]
    P += [PL([(882, 180), (934, 180)], BLU, name='Bus'), PL([(934, 174), (934, 372)], BLU, name='Bus')]
    P += [PL([(934, y), (950, y)], BLU, tail=True, name='Bus branch') for y in (174, 240, 306, 372)]
    P += [PL([(882, 402), (912, 402), (912, 438), (950, 438)], BLU, tail=True, name='Flow 7 to MQ'),
          PL([(560, 480), (560, 510)], DSH, 1.6, dash='dot', name='Collect down'),
          PL([(182, 528), (182, 510), (1098, 510), (1098, 528)], DSH, 1.6, dash='dot', name='Collect bus')]
    P += [PL([(x, 510), (x, 528)], DSH, 1.6, dash='dot', name='Collect drop') for x in (487, 793)]

    # nodes
    P += [R(52, 242, 136, 86, fill=C('white'), stroke=C('line'), sw=1.3, rx=8, name='User node'),
          ICON('person', 120, 268, 30, C('gray')),
          T(52, 288, 136, [line1('用户 / 客户端应用', 13, C('ink'), True, 18), line1('User / Client App', 10.5, C('soft'), False, 15)],
            align='c', name='User text')]
    P += node('Module 1', 240, 148, 180, 64, '会话与上下文管理器', 'Session / Context Management', CTX, n=1)
    P += node('Module 5', 470, 148, 170, 64, '记忆与状态存储', 'Memory / State Store', CTX, n=5)
    P += node('Module 4', 690, 148, 190, 64, '模型与工具路由器', 'Model / Tool Router', BLU, n=4)
    P += node('Module 2', 240, 252, 180, 64, '任务编排器', 'Task Orchestration', C('green', 'dark'), sw=2.2, n=2)
    P += node('Module 3', 240, 352, 180, 64, '提示词与策略层', 'Prompt / Policy Layer', GRY, sw=1.4, n=3)
    P += node('Module 6', 470, 352, 170, 64, '安全与 Guardrails', 'Safety / Guardrails', ORG, sw=2.0, fill=C('orange', 'fill'), n=6)
    P += node('Module 7', 690, 352, 190, 64, 'Agent 执行运行时', 'Agent Runtime', BLU, n=7)
    P += [R(240, 440, 640, 40, fill=C('white'), stroke=GRY, sw=1.4, rx=8, name='Module 8'),
          T(240, 450, 640, [([('可观测性 / 日志 / Trace', C('ink'), True), ('    Tracing · Metrics · Logs', C('soft'), False)], 13.5, 20)],
            align='c', name='Module 8 text'),
          NUM(8, 258, 460, C('green'), r=8, size=9.5)]
    ext = [('LLM 提供商', 'LLM Providers'), ('内部 API', 'Internal APIs'), ('外部工具', 'External Tools'),
           ('数据库 / 知识库', 'Database / Knowledge Base'), ('消息队列 / 后台工作进程', 'Message Queue / Background Workers')]
    for k, (t, s) in enumerate(ext):
        P += node(f'External {k+1}', 952, 146 + 66 * k, 272, 56, t, s, BLU if k < 4 else GRY)

    # labels last (on top of lines)
    for args in [('任务请求', 214, 276, 10.5, ORG), ('加载上下文', 339, 236, 10.5, CTX, 's'), ('读写记忆', 488, 263, 10.5, CTX),
                 ('记忆注入 · memory injection', 600, 291, 10.5, CTX), ('调用模型 / 工具', 807, 336, 10.5, BLU, 'e'),
                 ('组装提示词', 339, 338, 10.5, BLU, 's'), ('安全校验', 665, 375, 10, ORG),
                 ('collect · 观测数据供工程体系使用', 690, 513, 10.5, C('soft'))]:
        P += LABEL(*args)

    cards = [('评测框架', 'Evaluation · 使用 ⑧ 采集的 Trace', '评估 Agent 执行效果'),
             ('监控与指标', 'Monitoring · 基于 Metrics 跟踪', '运行时健康与性能'),
             ('配置 / 密钥', 'Config / Secrets · 集中管理', '各模块配置与访问凭据'),
             ('CI / CD', 'Pipeline · Harness 各模块的', '构建、测试与发布')]
    for k, (t, d1, d2) in enumerate(cards):
        x = 40 + 305 * k
        P += [R(x, 528, 285, 84, fill=C('white'), stroke=C('line'), rx=6, name=f'Card {k+1}'),
              R(x, 528, 285, 4, fill=C('green'), rx=0, name=f'Card {k+1} bar'),
              CHK(x + 24, 558, name=f'Card {k+1} check'),
              T(x + 42, 548, 230, [line1(t, 14, C('ink'), True, 20)], name=f'Card {k+1} title'),
              T(x + 24, 574, 252, [line1(d1, 12, C('muted'), False, 17), line1(d2, 12, C('muted'), False, 17)], name=f'Card {k+1} text')]

    P.append(T(40, 636, 1180, [
        line1(f'图例：{cw("orange")}色 = 任务请求入口与安全校验 · {cw("blue")}色 = 模型 / 工具调用 · '
              f'{cw("purple")}色 = 会话上下文与记忆 · 灰色虚线 = 可观测数据采集（collect）。', 11, C('soft'), False, 17),
        line1('①–⑧ 为 Harness 内部模块；④ 统一对接 LLM 提供商、内部 API、外部工具与数据库 / 知识库，⑦ 将后台任务投递到消息队列 / 后台工作进程。',
              11, C('soft'), False, 17)], name='Footnote'))
    return P
