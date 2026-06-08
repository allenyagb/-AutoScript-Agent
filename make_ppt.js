const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "第35组";
pres.title = "AutoScript Agent 答辩演示";

// ── Color Palette ──
const C = {
  teal: "028090",
  seafoam: "00A896",
  mint: "02C39A",
  lightBg: "F0FDFA",
  text: "1E293B",
  muted: "64748B",
  white: "FFFFFF",
  gray: "F1F5F9",
  border: "E2E8F0",
  dark: "0F172A",
  warn: "D97706",
  danger: "DC2626",
  green: "059669",
};

// ── Typography ──
const F = { title: "Cambria", body: "Calibri" };
const mkShadow = () => ({ type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.08 });

// ── Helpers ──
function addAccentBar(slide, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.06, h: 5.625,
    fill: { color: color || C.teal },
  });
}

function addSlideNumber(slide, num) {
  slide.addText(String(num), {
    x: 9.2, y: 5.15, w: 0.6, h: 0.35,
    fontSize: 10, fontFace: F.body, color: C.muted, align: "right",
  });
}

function addPageTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.65, y: 0.25, w: 8.8, h: 0.5,
    fontSize: 28, fontFace: F.title, color: C.text, bold: true, margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.65, y: 0.8, w: 1.2, h: 0.04, fill: { color: C.teal },
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.65, y: 0.95, w: 8.8, h: 0.3,
      fontSize: 12, fontFace: F.body, color: C.muted, margin: 0,
    });
  }
}

function addCard(slide, x, y, w, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: color || C.white },
    shadow: mkShadow(),
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 1 — 项目简介 (Title Slide)
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  // Top teal band
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 2.4, fill: { color: C.teal },
  });

  // Project name
  s.addText("AutoScript Agent", {
    x: 0.8, y: 0.4, w: 8.5, h: 0.8,
    fontSize: 40, fontFace: F.title, color: C.white, bold: true, margin: 0,
  });

  // Subtitle
  s.addText("基于大语言模型的 Ubuntu 自主任务执行智能体", {
    x: 0.8, y: 1.25, w: 8.5, h: 0.5,
    fontSize: 18, fontFace: F.body, color: C.lightBg, margin: 0,
  });

  // Tagline
  s.addText("自然语言驱动 Linux 运维  ·  多层安全检查  ·  自主决策执行", {
    x: 0.8, y: 1.8, w: 8.5, h: 0.4,
    fontSize: 13, fontFace: F.body, color: "99F6E4", margin: 0,
  });

  // Info cards row
  const cardY = 2.9, cardH = 2.3;
  // Left: Group info
  addCard(s, 0.65, cardY, 4.2, cardH, C.gray);
  s.addText([
    { text: "第 35 组", options: { fontSize: 26, fontFace: F.title, bold: true, color: C.teal, breakLine: true } },
    { text: "班级：23108011", options: { fontSize: 13, fontFace: F.body, color: C.muted, breakLine: true } },
    { text: "课程：Linux 系统管理与 Shell 编程", options: { fontSize: 12, fontFace: F.body, color: C.muted } },
  ], { x: 1.0, y: cardY + 0.3, w: 3.5, h: 1.8, valign: "top" });

  // Right: Members
  addCard(s, 5.15, cardY, 4.2, cardH, C.gray);
  s.addText("小组成员", {
    x: 5.5, y: cardY + 0.15, w: 3.5, h: 0.4,
    fontSize: 13, fontFace: F.body, bold: true, color: C.muted, margin: 0,
  });
  s.addText([
    { text: "杨  干    2310801124", options: { breakLine: true, fontSize: 15, fontFace: F.body, color: C.text } },
    { text: "何  亮    2310801104", options: { breakLine: true, fontSize: 15, fontFace: F.body, color: C.text } },
    { text: "吴俊宏    2310801118", options: { breakLine: true, fontSize: 15, fontFace: F.body, color: C.text } },
    { text: "李明松    201760130", options: { fontSize: 15, fontFace: F.body, color: C.text } },
  ], { x: 5.5, y: cardY + 0.55, w: 3.5, h: 1.6, paraSpaceAfter: 6 });

  addSlideNumber(s, 1);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 2 — 项目需求与目标
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "项目需求与目标");

  // ── "谁在使用" banner ──
  addCard(s, 0.65, 0.95, 8.7, 0.55, C.lightBg);
  s.addText("谁在使用？", {
    x: 0.85, y: 1.0, w: 1.2, h: 0.45,
    fontSize: 12, fontFace: F.body, bold: true, color: C.teal, valign: "middle", margin: 0,
  });
  const users = ["Linux 服务器管理员", "树莓派/边缘设备开发者", "小型网站维护人员", "运维新手"];
  users.forEach((u, i) => {
    const ux = 2.15 + i * 1.7;
    s.addShape(pres.shapes.RECTANGLE, {
      x: ux, y: 1.07, w: 1.5, h: 0.32, fill: { color: C.white },
    });
    s.addText(u, {
      x: ux, y: 1.07, w: 1.5, h: 0.32,
      fontSize: 9, fontFace: F.body, color: C.text, align: "center", valign: "middle",
    });
  });

  // Left column: Problems
  addCard(s, 0.65, 1.7, 4.2, 3.6, C.gray);
  s.addText("现有痛点", {
    x: 0.95, y: 1.8, w: 3.6, h: 0.35,
    fontSize: 14, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });

  const problems = [
    "命令记忆负担重 — grep/awk/sed 等参数组合繁多",
    "重复任务耗时 — 多服务器需手动逐台执行命令",
    "安全风险难控 — rm -rf / 等误操作后果灾难性",
    "脚本编写门槛高 — 需一定 Shell/Python 编程能力",
    "系统异常难发现 — 缺乏定时自动巡检机制",
  ];
  s.addText(problems.map((p, i) => ({
    text: p,
    options: { bullet: true, breakLine: i < problems.length - 1, fontSize: 11, fontFace: F.body, color: C.text, paraSpaceAfter: 6 },
  })), { x: 0.95, y: 2.2, w: 3.6, h: 2.9 });

  // Right column: Goals
  addCard(s, 5.15, 1.7, 4.2, 3.6, C.lightBg);
  s.addText("项目目标（具体可验证）", {
    x: 5.45, y: 1.8, w: 3.6, h: 0.35,
    fontSize: 14, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });

  const goals = [
    "自然语言驱动的文件操作（创建/读取/移动/删除）",
    "安全的 Shell 命令执行 + 多层安全策略检查",
    "自动检测拦截危险操作（20+ 条规则）",
    "多轮对话记忆，上下文理解与代词指代",
    "执行失败自动重试（最多3次）+ LLM自我修正",
    "集成 LangChain 框架，标准化 Tool Calling",
    "定时系统巡检（CPU/内存/磁盘/僵尸进程）",
  ];
  s.addText(goals.map((g, i) => ({
    text: g,
    options: { bullet: true, breakLine: i < goals.length - 1, fontSize: 11, fontFace: F.body, color: C.text, paraSpaceAfter: 5 },
  })), { x: 5.45, y: 2.2, w: 3.6, h: 2.9 });

  addSlideNumber(s, 2);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 3 — 系统设计
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "系统设计", "四层架构 · 八大模块");

  // Architecture layers — 4 horizontal bars
  const layers = [
    { name: "用户交互层", color: C.teal, mods: "agent_cli.py 交互终端  |  patrol_task.py 定时巡检  |  tests/ 测试套件" },
    { name: "智能体核心层", color: C.seafoam, mods: "agent.py (LangChainAgent)  |  chat_model.py (ChatQwen)" },
    { name: "工具执行层", color: C.mint, mods: "tools.py (6个LangChain工具)  |  safety_checker.py  |  script_executor.py" },
    { name: "基础设施层", color: "0D9488", mods: "DashScope API (qwen3.7-max)  |  LangChain 框架  |  sandbox_workspace/" },
  ];

  layers.forEach((l, i) => {
    const y = 1.2 + i * 0.85;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.65, y, w: 8.7, h: 0.72,
      fill: { color: C.white },
      shadow: mkShadow(),
    });
    // Color indicator
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.65, y, w: 0.06, h: 0.72, fill: { color: l.color },
    });
    s.addText(l.name, {
      x: 0.9, y: y + 0.05, w: 1.5, h: 0.28,
      fontSize: 12, fontFace: F.body, bold: true, color: l.color, margin: 0,
    });
    s.addText(l.mods, {
      x: 0.9, y: y + 0.34, w: 8.2, h: 0.3,
      fontSize: 10, fontFace: F.body, color: C.muted, margin: 0,
    });
  });

  // Bottom: 8 module cards grid
  const modules = [
    "chat_model\nAI对话模型", "agent\n智能体核心", "tools\n工具集(6个)",
    "safety_checker\n安全检查", "script_executor\n脚本执行", "qwen_chat\n流式对话",
    "agent_cli\n交互终端", "patrol_task\n定时巡检",
  ];
  const cardW = 1.95, cardH = 0.48, startX = 0.65, startY = 4.5, gap = 0.1;
  modules.forEach((mod, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const cx = startX + col * (cardW + gap), cy = startY + row * (cardH + gap * 1.5);
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: C.gray },
    });
    const lines = mod.split("\n");
    s.addText([
      { text: lines[0], options: { fontSize: 9, fontFace: F.body, bold: true, color: C.teal, breakLine: true } },
      { text: lines[1] || "", options: { fontSize: 7, fontFace: F.body, color: C.muted } },
    ], { x: cx + 0.1, y: cy + 0.03, w: cardW - 0.2, h: cardH - 0.06, valign: "middle" });
  });

  addSlideNumber(s, 3);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 4 — Linux 技术使用情况
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "Linux 技术使用情况", "项目共使用 8+ 种课程相关技术，远超最低要求的 4 种");

  const techs = [
    ["Bash", "script_executor.py / tools.py", "自动化执行 Shell 命令和脚本"],
    ["Python", "全部模块", "核心开发语言，实现智能体框架"],
    ["grep / 正则(re)", "safety_checker.py", "过滤匹配危险命令模式（20+条规则）"],
    ["AST 静态分析", "safety_checker.py", "Python 语法树分析，检测 eval/subprocess 等危险调用"],
    ["subprocess", "script_executor.py", "安全执行脚本，捕获 stdout/stderr，超时控制"],
    ["crontab", "patrol_task.py + 系统 crontab", "定时触发系统巡检，实现自动化运维"],
    ["Git", "项目版本管理", "16 次 commit 管理全流程开发迭代"],
    ["LangChain", "agent.py / chat_model.py", "AI Agent 框架，Tool Calling + 消息管理"],
  ];

  // Table
  const tableRows = [
    [
      { text: "技术", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
      { text: "使用位置", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
      { text: "作用", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
    ],
    ...techs.map((row, i) =>
      row.map(text => ({
        text,
        options: {
          fontSize: 10, fontFace: F.body, color: C.text,
          fill: { color: i % 2 === 0 ? C.white : C.gray },
        },
      }))
    ),
  ];

  s.addTable(tableRows, {
    x: 0.65, y: 1.3, w: 8.7,
    colW: [1.5, 2.9, 4.3],
    rowH: [0.35, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38],
    border: { pt: 0.5, color: C.border },
  });

  // Highlight box
  addCard(s, 0.65, 4.6, 8.7, 0.65, C.lightBg);
  s.addText("课程关联：Bash 自动化 · 正则文本处理 · 进程管理(subprocess) · 定时任务(crontab) · 版本管理(Git) · 系统巡检(CPU/内存/磁盘)", {
    x: 0.95, y: 4.7, w: 8.1, h: 0.45,
    fontSize: 11, fontFace: F.body, color: C.teal, valign: "middle",
  });

  addSlideNumber(s, 4);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 5 — 核心功能展示
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "核心功能展示", "两大核心能力：自然语言文件操作 · 安全Shell命令执行");

  // Feature 1 card
  addCard(s, 0.65, 1.3, 4.2, 3.9, C.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.65, y: 1.3, w: 4.2, h: 0.06, fill: { color: C.mint },
  });
  s.addText("功能一：自然语言文件操作", {
    x: 0.95, y: 1.5, w: 3.6, h: 0.35,
    fontSize: 14, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });
  s.addText([
    { text: "用户输入自然语言 → Agent 自主调用工具", options: { breakLine: true, fontSize: 10, fontFace: F.body, color: C.muted, paraSpaceAfter: 8 } },
    { text: "write_file — 创建/覆盖文件", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "read_file — 读取文件内容", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "list_files — 列出工作区文件", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "move_file — 移动/重命名文件", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "delete_file — 删除文件（含realpath边界检查）", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
  ], { x: 0.95, y: 1.95, w: 3.6, h: 3.0 });

  // Feature 2 card
  addCard(s, 5.15, 1.3, 4.2, 3.9, C.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.15, y: 1.3, w: 4.2, h: 0.06, fill: { color: C.mint },
  });
  s.addText("功能二：安全Shell命令执行", {
    x: 5.45, y: 1.5, w: 3.6, h: 0.35,
    fontSize: 14, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });
  s.addText([
    { text: "命令 → 安全检查 → 执行/拦截 → 返回结果", options: { breakLine: true, fontSize: 10, fontFace: F.body, color: C.muted, paraSpaceAfter: 8 } },
    { text: "正则匹配：20+ 条危险命令黑名单", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "AST 分析：Python 脚本语法树检测", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "三级风险：safe / warning / dangerous", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "dangerous 级别直接拒绝执行", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.danger } },
    { text: "沙箱工作区隔离 + 30s超时 + 10MB输出截断", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
  ], { x: 5.45, y: 1.95, w: 3.6, h: 3.0 });

  addSlideNumber(s, 5);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 6 — 测试与验证
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "测试与验证", "4 个测试套件 · 覆盖功能/异常/边界/安全");

  // Top: test summary cards
  const tests = [
    { title: "功能测试", count: "7项", status: "全部通过", items: "文件CRUD · 系统信息 · 多轮对话 · 文件分类" },
    { title: "异常测试", count: "5项", status: "全部通过", items: "文件不存在 · 权限不足 · 网络断开 · 语法错误" },
    { title: "边界测试", count: "4项", status: "全部通过", items: "3s超时控制 · 空文件 · 10MB截断 · 中文路径" },
    { title: "安全测试", count: "5项", status: "全部拦截", items: "rm -rf / · mkfs · curl|sh · dd · systemctl" },
  ];

  tests.forEach((t, i) => {
    const cx = 0.65 + i * 2.25;
    addCard(s, cx, 1.25, 2.05, 1.85, C.white);
    s.addText(t.title, {
      x: cx + 0.15, y: 1.33, w: 1.75, h: 0.3,
      fontSize: 13, fontFace: F.body, bold: true, color: C.teal, margin: 0,
    });
    s.addText(t.count, {
      x: cx + 0.15, y: 1.6, w: 1.0, h: 0.4,
      fontSize: 22, fontFace: F.title, bold: true, color: C.text, margin: 0,
    });
    const isPass = t.status.includes("通过") || t.status.includes("拦截");
    s.addText(t.status, {
      x: cx + 1.1, y: 1.68, w: 0.8, h: 0.25,
      fontSize: 9, fontFace: F.body, color: isPass ? C.green : C.danger, margin: 0,
    });
    s.addText(t.items, {
      x: cx + 0.15, y: 2.1, w: 1.75, h: 0.8,
      fontSize: 8, fontFace: F.body, color: C.muted,
    });
  });

  // Bottom: Bug fixes
  addCard(s, 0.65, 3.4, 8.7, 1.85, C.gray);
  s.addText("典型 Bug 修复案例", {
    x: 0.95, y: 3.5, w: 4, h: 0.3,
    fontSize: 13, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });

  const bugs = [
    { title: "API 超时死循环", fix: "退避重试(2s→4s→8s) + 超时错误不污染对话历史" },
    { title: "工作区路径不一致", fix: "ScriptExecutor 改用 __file__ 相对路径，替代 os.getcwd()" },
    { title: "delete_file 路径穿越", fix: "os.path.realpath() + 前缀匹配，拦截 ../ 越界" },
  ];

  bugs.forEach((b, i) => {
    const by = 3.9 + i * 0.42;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.95, y: by, w: 0.06, h: 0.3, fill: { color: C.warn },
    });
    s.addText(b.title, {
      x: 1.15, y: by, w: 2.2, h: 0.3,
      fontSize: 10, fontFace: F.body, bold: true, color: C.text, margin: 0,
    });
    s.addText(b.fix, {
      x: 3.35, y: by, w: 5.7, h: 0.3,
      fontSize: 10, fontFace: F.body, color: C.muted, margin: 0,
    });
  });

  addSlideNumber(s, 6);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 7 — 开发过程与版本迭代
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "开发过程与版本迭代", "16 次 Git Commit · 从原型到完整 Agent 系统");

  // Timeline bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.65, y: 1.45, w: 8.7, h: 0.04, fill: { color: C.border },
  });

  const milestones = [
    { date: "5.21", ver: "v0.1", desc: "Qwen对话\n流式输出" },
    { date: "5.22", ver: "v0.2", desc: "核心模块\n文件操作" },
    { date: "5.22", ver: "v0.3", desc: "LangChain重构\n6个Tools" },
    { date: "6.06", ver: "v0.4", desc: "流式美化\n终端输出" },
    { date: "6.06", ver: "now", desc: "Bug修复\n测试完善" },
  ];

  milestones.forEach((m, i) => {
    const mx = 1.2 + i * 1.75;
    s.addShape(pres.shapes.OVAL, {
      x: mx + 0.35, y: 1.32, w: 0.3, h: 0.3, fill: { color: i === 4 ? C.mint : C.teal },
    });
    s.addText(m.ver, {
      x: mx - 0.1, y: 1.65, w: 1.2, h: 0.25,
      fontSize: 11, fontFace: F.body, bold: true, color: C.text, align: "center", margin: 0,
    });
    s.addText(m.desc, {
      x: mx - 0.1, y: 1.88, w: 1.2, h: 0.5,
      fontSize: 9, fontFace: F.body, color: C.muted, align: "center",
    });
  });

  // Version table
  const verHeader = [
    { text: "版本", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, fontFace: F.body } },
    { text: "完成内容", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, fontFace: F.body } },
    { text: "关键突破", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, fontFace: F.body } },
  ];
  const verData = [
    ["v0.1.x", "Qwen 大模型对话 + SSE 流式输出", "DashScope API 适配"],
    ["v0.2.x", "核心模块：写文件/移动文件/执行文件 + 测试", "模块化解耦设计"],
    ["v0.3.x", "LangChain 重构 + 6个Tools + SafetyChecker", "Agent + Tool Calling 架构"],
    ["v0.4.x", "流式美化 + 错误重试退避 + Bug 修复", "智能重试 + 路径一致性修复"],
  ];
  const verRows = [
    verHeader,
    ...verData.map((row, i) =>
      row.map(text => ({
        text,
        options: {
          fontSize: 9, fontFace: F.body, color: C.text,
          fill: { color: i % 2 === 0 ? C.gray : C.white },
        },
      }))
    ),
  ];

  s.addTable(verRows, {
    x: 0.65, y: 2.55, w: 8.7,
    colW: [1.2, 4.5, 3.0],
    border: { pt: 0.5, color: C.border },
  });

  // Git stats highlight
  addCard(s, 0.65, 4.65, 8.7, 0.6, C.lightBg);
  s.addText("Git 统计：16 commits  ·  30+ Python 文件  ·  约 2,255 行代码  ·  功能分支开发模式", {
    x: 0.95, y: 4.73, w: 8.1, h: 0.45,
    fontSize: 12, fontFace: F.body, color: C.teal, valign: "middle",
  });

  addSlideNumber(s, 7);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 8 — 小组分工与总结
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  addAccentBar(s, C.teal);
  addPageTitle(s, "小组分工与总结", "第35组 · 各成员实际贡献明确");

  // Division table
  const divHeader = [
    { text: "成员", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
    { text: "负责内容", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
    { text: "完成情况", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11, fontFace: F.body } },
  ];
  const divData = [
    ["杨  干", "核心模块开发 · LangChain框架集成 · 安全模块设计 · CLI终端", "✅ 全部完成"],
    ["何  亮", "ChatModel实现 · DashScope API适配 · 流式输出模块", "✅ 全部完成"],
    ["吴俊宏", "测试套件编写 · 异常/边界测试 · 自动化验证", "✅ 全部完成"],
    ["李明松", "文档撰写 · 项目报告 · PPT制作 · 答辩准备", "✅ 全部完成"],
  ];
  const divRows = [
    divHeader,
    ...divData.map((row, i) =>
      row.map((text, j) => ({
        text,
        options: {
          fontSize: 10, fontFace: F.body, color: C.text,
          fill: { color: i % 2 === 0 ? C.white : C.gray },
          bold: j === 0,
        },
      }))
    ),
  ];

  s.addTable(divRows, {
    x: 0.65, y: 1.2, w: 5.5,
    colW: [1.2, 2.9, 1.4],
    border: { pt: 0.5, color: C.border },
  });

  // Summary
  addCard(s, 6.45, 1.2, 2.9, 1.95, C.lightBg);
  s.addText("项目成果总结", {
    x: 6.65, y: 1.3, w: 2.5, h: 0.3,
    fontSize: 12, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });
  s.addText([
    { text: "8 个功能模块", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "6 个 LangChain 工具", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "20+ 条安全规则", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "4 套测试，25+用例", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: F.body, color: C.text } },
    { text: "16 次 Git Commit", options: { bullet: true, fontSize: 10, fontFace: F.body, color: C.text } },
  ], { x: 6.65, y: 1.65, w: 2.5, h: 1.5 });

  // Learnings & Improvements
  addCard(s, 0.65, 3.4, 8.7, 1.85, C.gray);
  s.addText("收获", {
    x: 0.95, y: 3.5, w: 3.5, h: 0.28,
    fontSize: 12, fontFace: F.body, bold: true, color: C.teal, margin: 0,
  });
  s.addText("Linux进程管理 · Shell脚本安全执行 · 正则表达式应用 · AST静态分析 · crontab自动化 · Git协作 · AI Agent开发", {
    x: 0.95, y: 3.78, w: 8.1, h: 0.3,
    fontSize: 10, fontFace: F.body, color: C.text, margin: 0,
  });

  s.addText("不足与改进", {
    x: 0.95, y: 4.18, w: 3.5, h: 0.28,
    fontSize: 12, fontFace: F.body, bold: true, color: C.warn, margin: 0,
  });
  s.addText("沙箱隔离可引入 Docker 容器化 · 安全规则可补充白名单机制 · 工具调用可支持并行执行 · 后续增加 Web 管理界面", {
    x: 0.95, y: 4.46, w: 8.1, h: 0.3,
    fontSize: 10, fontFace: F.body, color: C.text, margin: 0,
  });

  // Thank you
  s.addText("感谢聆听", {
    x: 0.65, y: 4.95, w: 3.5, h: 0.4,
    fontSize: 16, fontFace: F.title, color: C.teal, italic: true, margin: 0,
  });

  addSlideNumber(s, 8);
}

// ── Write ──
pres.writeFile({ fileName: "答辩PPT.pptx" }).then(() => {
  console.log("✅ 答辩PPT.pptx 生成成功！");
}).catch(err => {
  console.error("❌ 生成失败:", err);
  process.exit(1);
});
