# World Model Memory Atlas · 世界模型记忆图谱

**用时间轴读世界模型：124 篇论文、8 条技术路线、每条路线各自的时钟。**

在线打开：**https://ghf2458526136-sys.github.io/awesome-world-model-memory/**

一张可交互的时间轴地图，回答一个具体问题：**长视频世界模型到底怎么记住并找回它看过的东西。**
每篇论文落在一个"时间 × 路线"的坐标上，点开有机制走读、关键公式、官方演示和链接。

[![Papers](https://img.shields.io/badge/papers-124-2f6feb)](#)
[![Lanes](https://img.shields.io/badge/routes-8-0e7c86)](#)
[![Updated](https://img.shields.io/badge/updated-2026--10-21-4a5563)](#)
[![License](https://img.shields.io/badge/data-CC%20BY%204.0-e0891a)](DATA-LICENSE.md)
[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

## 为什么做这个

现有的世界模型清单都是 markdown 长表：能查，但看不出**谁接在谁后面**、**哪条路线在什么时候分叉**、**同一时期的方案在争什么**。

这张图把 124 篇论文按 8 条路线铺开，每条路线有自己独立的时间轴——因为不同路线的论文密度差得很远，共用一条时间轴会让早期几年空成一片，而 2026 年 10 月挤成一团。

- **框架层**（15）：整套系统与闭源产品
- **代码世界模型**（14）：代码定义世界状态，视频模型只负责渲染
- **位置时间寻址**（18）：改 RoPE 位置、重排槽位、锚定 sink
- **几何位姿寻址**（25）：点云、视锥、surfel 这类显式空间索引
- **内容学习寻址**（11）：外部检索库与学习式路由
- **参数化记忆**（9）：把历史写进权重或测试时适配参数
- **训练侧**（14）：蒸馏、因果化、少步采样的训练配方
- **评测基准**（18）：测什么信号、怎么判回访

## 每篇论文有什么

点开任意卡片，右侧面板给四层信息：

| 层 | 内容 |
|---|---|
| 直白讲解 | 一段口语化说明，给第一次接触的人 |
| 机制详解 | 定位 / 输入输出 / 做法步骤 / 关键公式 / 训练与推理 / 与已有做法的差别 / 代价与局限，公式用 KaTeX 渲染 |
| 关键数字 | 论文自报的参数量、帧数、显存、FPS；我们自测的数字单独标出，不与论文混用 |
| 素材与链接 | 官方项目页的演示视频/图片直链、arXiv、代码、权重 |

## 怎么用

- 点卡片开面板，`←` `→` 切换相邻论文
- `/` 搜索标题、机制、标签
- 滚轮或拖拽平移，`Ctrl` + 滚轮缩放，双击空白回到全览
- 顶部搜索框输入路线名可高亮整条泳道
- 绿色标签 = 免训（training-free），带呼吸光圈的是汇报主线要讲的论文

## 贡献

加一篇论文 = 在 `research-map.yaml` 里加一条，然后重新生成页面。字段说明、校验方式、PR 规范见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

```bash
python build_map.py research-map.yaml index.html "World Model Memory Atlas" ""
```

脚本会校验 arXiv 编号格式与素材路径，缺文件会直接列出来，不会静默生成坏页面。

## 仓库结构

```
index.html            生成好的单文件页面（KaTeX 与字体已内联，离线可用）
research-map.yaml     唯一数据源，每篇论文一条
research-map-online.yaml  线上版（把本地视频路径换成官方直链）
build_map.py          生成器：校验数据 → 排版 → 输出 HTML
panel_detail.js/.css  详情面板的机制详解模块
katex.min.js / katex_inline.css  公式渲染（内联进页面）
```

## 和其它 world model 清单的区别

| 项目 | 形式 | 侧重 |
|---|---|---|
| 本项目 | 可交互时间轴 + 方法走读 | 长视频世界模型的**回溯记忆与记忆寻址** |
| knightnemo/Awesome-World-Models | markdown 清单 | 通用世界模型全景 |
| LMD0311/Awesome-World-Model | markdown 清单 | 自动驾驶 |
| leofan90/Awesome-World-Models | markdown 清单 | 机器人与定义梳理 |
| OpenMOSS/Awesome-WAM | markdown 清单 | 世界动作模型 |

我们不试图覆盖所有世界模型，只把一个细分做深：**记忆怎么存、怎么找、为什么会失效**。

## 数据可信度

- 每篇的 arXiv 编号与标题都抓 arXiv 原文核对过，编号与标题不符的会标出来
- 论文自报数字与"官方 demo 上自测的数字"分栏存放，不混用
- 找不到官方演示的条目标注为"无演示素材"，不用文字描述冒充画面
- 机制详解由模型按摘要与方法撰写，公式标注是否来自原文

## 许可

- 代码（`build_map.py`、面板模块）：MIT，见 [LICENSE](LICENSE)
- 数据与文字（`research-map.yaml`、机制详解、页面内容）：CC BY 4.0，见 [DATA-LICENSE.md](DATA-LICENSE.md)
