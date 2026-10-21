# 贡献指南

加一篇论文只需要改一个文件：`research-map.yaml`。生成器负责排版、校验和输出页面。

## 最短路径

```bash
git clone https://github.com/ghf2458526136-sys/awesome-world-model-memory.git
cd awesome-world-model-memory

# 1. 在 research-map.yaml 的 nodes 列表末尾加一条（字段见下）
# 2. 本地生成，检查有没有报错
python build_map.py research-map.yaml index.html "World Model Memory Atlas" ""

# 3. 打开 index.html 看卡片位置、标签、面板是否正常
# 4. 提交
git checkout -b add-<short-name>
git add research-map.yaml index.html
git commit -m "add <Paper Name> (<arXiv id>)"
git push origin add-<short-name>
```

然后在 GitHub 上开 PR，说明这篇为什么属于当前路线。同一条路线里位置排错不要紧，合并时我会核对。

## 一条论文的字段

```yaml
- id: worldtrace              # 必填，小写连字符，全局唯一，用作卡片锚点
  title: WorldTrace           # 必填，页面上显示的名字（可用简称）
  arxiv: 2608.07408           # 强烈建议填，只写编号不写 URL；生成器会校验格式
  date: 2026-08-01            # 必填，YYYY-MM-DD；只知道月份就写当月 1 号
  precision: month            # 可选，month 表示日期只到月，卡片上不显示日
  lane: 位置时间寻址           # 必填，八条泳道之一，见表格
  branch: 重排位置             # 可选，泳道内的子分支，空字符串表示主支
  parent: rolling-forcing     # 可选，另一个 id；画一条"机制同构"的连线
  one_liner: 记忆失效首因是地址失效      # 必填，一句话，建议不超过 25 字
  mechanism: 把已带 RoPE 的 key 反旋转回内容空间…   # 可选，一两句话的方法摘要
  tags: [槽位重编号, 免训外挂]           # 可选，2-3 个，每个不超过 6 个汉字
  training: 免训               # 需训 / 免训 / 推理期技巧 / 不适用
  status: 精读                 # 精读 / 速读
  key_numbers: [3000 帧, 640x352@10fps]  # 可选，论文自报的数字
  media:                       # 可选，演示视频或图片
    - https://example.com/demo.mp4
  links:                       # 可选，但建议至少有 arXiv
    - https://arxiv.org/abs/2608.07408
  note: 只给到月份 2026-08      # 可选，任何需要提醒读者的事
```

### 八条泳道

| lane | 收什么 |
|---|---|
| `框架层` | 完整系统、闭源产品、把状态与渲染分开的整体方案 |
| `代码世界模型` | 代码定义世界状态、引擎执行规则、视频模型只做渲染 |
| `位置时间寻址` | 改 RoPE 位置、重排槽位、attention sink、上下文重排 |
| `几何位姿寻址` | 点云、视锥、surfel、深度等显式空间索引 |
| `内容学习寻址` | 外部检索库、向量记忆、学习式路由与门控 |
| `参数化记忆` | 把历史写进权重、测试时训练、适配器记忆 |
| `训练侧` | 蒸馏、因果化、少步采样、训练课程等配方 |
| `评测基准` | 测什么信号、怎么判长程一致与回访 |

拿不准归哪条，就在 PR 里写两个候选和理由，不要硬塞。

## 素材规则

1. **只用官方来源**：项目页、官方仓库、作者主页。二手转载的链接不收。
2. **直链要能直接播**：`.mp4` / `.webm` / `.png` / `.jpg`，优先用官方服务器地址，不要用带签名会过期的临时链接。
3. **本地文件用相对路径**：`demos/<项目>/<文件名>`，同时把文件放进 `demos/` 对应目录。
4. **不要用文字描述冒充画面**：找不到官方演示就留空，生成器会在面板里如实显示"无演示素材"。

## 数字规则

- `key_numbers` 只放论文自己报的数字
- 你在官方 demo 上自己算出来的指标，放 `self_measured`，页面会单独标"非论文指标"
- 两者不能混在一栏，这是这个项目最基本的诚实要求

## 提交前自检

```bash
python build_map.py research-map.yaml index.html "World Model Memory Atlas" ""
```

看到 `wrote index.html nodes=N lanes=8` 且没有 `缺素材` 列表，就可以提交。
如果出现 `缺素材`，说明 `media` 里的路径或链接有问题：本地路径要确认文件存在，网络链接要确认能直接打开。

## PR 检查清单

- [ ] `id` 没和现有条目重复
- [ ] `arxiv` 编号与 `title` 对得上（先去 `arxiv.org/abs/<id>` 看一眼）
- [ ] `date` 与 arXiv 编号里的年月一致；不一致的话在 `note` 里说明原因
- [ ] `lane` 是八条之一，`branch` 与同泳道其他条目用词一致
- [ ] `tags` 描述机制，不写"效果好""很重要"这类评价
- [ ] 重新生成过 `index.html`，本地打开确认卡片位置正常
