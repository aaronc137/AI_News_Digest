# AI 日报图文一体出图架构 v2

适用于默认 ImageGen 与 Artist Lottery。参考 2026-09-06 周报的图文一体范式，继承 `DESIGN_PRINCIPLES.md` 的 Discover → Define → Enrich → Deliver，不固定周报的柔光、纸张、微缩人物或配色，也不固定今天的卡拉瓦乔。用户当次要求优先。

## 1. 先定命题，再抽取视觉机制

每张图只表达一个读者能感知的变化：谁的什么产品，让哪一步工作变了，仍有哪些边界。日报必须保留日级特殊性，不把周报的跨事件大命题直接搬来。

必需输入：

|字段|要求|
|---|---|
|report_window|本期实际起止日期；补读不伪装为当天发布。|
|thesis|公司/产品＋具体变化＋读者影响，一句话。|
|evidence|新闻ID、原始URL、发布日期、证据性质与适用边界；元数据不全部上图。|
|visual_action|一个可见动作或关系：交接、局部替换、穿越、检查、接通、等待等。|
|exact_text|一个短主标题、一个产品锚点、至多一句限定或批判判断。产品已在标题中则不再重复锚点。|
|composition|动作、主体、文字共用一条阅读路径；前后景、观看角度与留白有明确理由。|
|style_mechanisms|来自本次Lottery契约的空间、材料、光或节奏机制，不只列艺术家名字。|
|constraints|16:9、中文可读、无误导事实、无假UI、无身份人脸或无语境文化符号。|

输入不足先回到编辑阶段，不让图像模型编补产品功能、数字、日期和UI承诺。证据字段可由编辑补齐；不能因JSON形状完整就声称核验通过。

## 2. 日报文字预算

- 图上优先是**短判断**，不是字号最大的长产品清单。产品名作短锚点，不与标题抢第一阅读层。
- 主标题建议12–22个汉字、最多两行；锚点一行；限定/批判判断建议14–26字。总中文正文尽量不超过50字，英文品牌另计，但仍须实际检查占宽。
- 不再默认同时堆日期、编号、品牌串、大标题、副标题、批判尾注和解释标签。日期如保留只出现一次；能删的元信息就删。
- 图上必须有边界时，让它进入主标题或唯一一句限定，不强行添加第四层文字。交易阶段、试验范围、数据口径等不能为了短而失真。
- 用准确字体描述而不是“高级字体”：默认几何无衬线中文的当代编辑节奏；Lottery机制需要时可用克制衬线标题，但说明文字保持简洁。禁止每次回到满幅巨型宋体＋暗桌面。
- 以约375px宽的手机展示验收：主判断无需放大可读；次级信息若读不清，先删字和换排布，不继续缩字号。

## 3. 图像不是背景，文字不是贴纸

先写动作，再决定留白在哪里。标题可以沿折纸轮廓、通道缺口、主体上方或对角空间进入；不固定“左字右图”或“上半标题、下半静物”。文字保持正常阅读方向，不能为了融合而扭曲到难读。

系列靠字体家族、色彩关系、边距和材料逻辑统一；三图至少在观看角度、主体关系、空间骨架中有两项不同。不要把每条新闻都翻译成桥、手、笔、纸、桌面、窗光；这些只在有语义必要时使用。小人物与巨物的尺度对照是可选手法，不是新固定模板。

风格服从命题。抽到暗光机制，光必须选择关键动作；抽到重复与节奏，重复必须解释供给、流程或关系；不能只加同色颗粒。不要因某一图的审美成功而给后两图换字复用。

## 4. 可直接填充的 Prompt

```text
scene_or_backdrop:
Create a complete 16:9 Chinese editorial illustration with integrated typography.
Report window: {report_window}. Thesis: {thesis}.
Establish {viewing_condition}; avoid a generic background awaiting a headline.

subject:
Show {visual_action} through {objects_and_spatial_relation}.
The image must communicate {reader_change} even with the headline hidden.
This is a conceptual illustration, not a product screenshot or proof of functionality.

key_details:
Use {style_mechanism_1} and {style_mechanism_2} to reveal the decisive relationship.
Place the exact title in {meaningful_negative_space}, along the same reading path.
Exact title: {short_title}
Exact product anchor, only if not repeated in title: {product_anchor}
One qualification or critical line: {boundary_line}
Use precise contemporary Chinese typography, large mobile-readable type and deliberate hierarchy.
Material and color: {content_relevant_material_and_color}; not inherited automatically from the last issue.

constraints:
Only render supplied exact text. No invented numbers, scores, labels, UI controls or logos.
No unrelated decoration, glow or stock technology symbols; no text occlusion.
Do not imply partnership through a multiplication sign, completed deployment through all-green checks,
or unrestricted permission through a symbolic approval prop.
At least 5% safe margins. Distinct composition from the other two images.
Evidence boundaries to preserve: {evidence_boundaries}.

output_intent:
One mobile-readable trend entrance for the daily report; full evidence remains in the article.
Generate image and typography together. No HTML screenshot or separate title overlay.
```

本模板是编辑骨架，不是把未填变量直接发给ImageGen。Prompt归档保留本期来源ID、完整文本、生成文件路径、版本和评审状态；禁止旧图冒充新一期生成结果。

## 5. 验收与止损

1. **遮标题测试**：遮住标题后，可见动作是否仍在表达目标关系？不要求无文字就猜出产品名。
2. **换新闻测试**：换成任意新闻仍完全成立，说明图像太通用；重写动作，不只换道具。
3. **事实测试**：隐喻不新增产品承诺；授权标签、成功勾、图表与合作符号都可能误导。
4. **手机测试**：文字正确、大字可读、无遮挡，第一阅读层只有一个判断。
5. **系列测试**：三张不是同一布景、角度和标题位置；统一气质而非复制画面。
6. **独立评审**：只给最终图、趋势和契约；保留评分、finding与修复。按原规则9分门槛，不追着评分换评审。

通常1–2轮修复后若不收敛，退回动作/构图阶段或更换方向，不继续在同一静物上加标签。记录未通过，不假造独立QA或用户确认。

## 6. 9.8–9.9 的改写示例（未重新出图）

|趋势|图上短判断|产品锚点|唯一限定|动作与构图|
|---|---|---|---|---|
|代办衔接|问完，下一步也有人接|豆包 · Muse|交给AI，不等于放弃确认|俯视一条未完成的服务路径，在交接点等待人确认；不复刻具体授权界面。|
|减少返工|只改这一处，其余别动|Images · Suno · Lovable|第一稿惊艳，第三轮还要稳|近景局部替换，周边连续形状保持不变；文字利用修改动作留下的负空间，不再三板陈列。|
|真实采用|上线只是起点，用起来才算|Grok Bot · Stripe Kai|发布速度不等于持续使用|远景入口到真实工作台之间仍有引导动作；不以全绿勾证明采用成功。|

这些示例不改变已发布日报与图片。下一次实际生成须按当天内容重写动作并重新抽取风格。
