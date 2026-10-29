# 墨卷 · 对抗式审查（2026-10-29）

范围：`ink_scroll/web/index.html`（5814 行）、`server.py`、`tools/test.js`、`tools/rsi/score.mjs`、`docs/REVIEW.md`。行号以 2026-10-29 09:05 读到的版本为准。
方法：Playwright（chromium-1217，脚本在 `/tmp/adv/*.js`，日志 `/tmp/adv/{mem,edge2,edge}.log`）+ curl。标「推测」的是只读代码没跑出来的；标「未完成」的是脚本中途被浏览器崩溃/会话超时打断、没拿到结果的。

## 1. 假测试清单（断言绿 ≠ 功能可用）

统计：`test.js` 里 `S.xxx =` 直接赋值 81 处（其中对象/常量打桩 48 处，`grep -nE "S\.[a-z0-9_.]+\s*=" tools/test.js`）；「可进入」类断言 31 条（L468-476 23 条、L1124-1127 4 条、L1179-1182 4 条）。

| # | 位置 | 实际证明了 | 没证明 |
|---|---|---|---|
| 1 | L123 `ok('首屏在 15s 内完成载入', true, …)` | 字面恒真 | 载入时间（真超时由 waitForFunction 抛错崩整套，而不是这条变红） |
| 2 | L146 与 L150 | 同一个 `modeCards.length` 断言两遍（42 与 ≥24） | 第二条纯凑数 |
| 3 | L468-476 ×23 `模式 X 可进入且不报错` | `wM(m)` 把 `S.mode` 字符串设成 m，且无 console.error | 任一模态的光圈是否随输入动；nfc/light/eyes/gamepad/hid 在无头机上没有任何硬件 |
| 4 | L283-297 静默翻页 | `S.audio={on:true,level:0}`、`since=now-21000` 手工塞进去后 processFrame 分支会调 changeScene | 麦克风安静检测本身（audio.level 从未由真实管线产生） |
| 5 | L705-707 IR | `ir.has ? mode==='ir' : mode==='ir'` 两个分支完全相同 | 任何东西；是披着条件外衣的恒真 |
| 6 | L710-715 NFC | 测试自己装了 `window.NDEFReader` 桩，然后断言 `'NDEFReader' in window` | 断言的是自己刚放进去的桩，与应用无关 |
| 7 | L719 环境光 | `lx.sensor ? true : lx.ok===false` | 有传感器时无条件通过 |
| 8 | L306-312 日课题款 | `cap` 由测试自己调 `dailySeed().label` 算出再用正则验自己 | 分享卡上是否真的印了日期（从未读分享卡 DOM/canvas） |
| 9 | L679-702 HID / BLE | `S.hid`/`S.ble` 整个对象打桩后直接调 `hidReport`/`bleValue` | `hidStart` 的 `requestDevice`→open→addEventListener 路径一行都没跑 |
| 10 | L929-950 吹墨 | `S.audio.level=0.75` 硬编码 + 手动调 6 次 `M.blow.spot()` | 麦克风→level 的链路；渲染循环里的行为 |
| 11 | L1031-1046 节拍 | 测试每轮把 `S.beat2.last=now-500` 写死，于是 BPM 必然≈120 | 阈值 `60≤bpm≤240` 松到任何估计器都过；通量检测的真实灵敏度 |
| 12 | L766-768 点云「光位改变视角」 | 两次快照 260ms 内任一像素/均值不同 | L836-850 自证点云随时间自己漂移，所以不动光也会过，断言空洞 |
| 13 | L797-807、L867-870 头部视差/3D 耦合 | `S.face`/`S.audio`/`S.hlm=[{}]` 全部打桩后 drawCloud 读到了字段 | 识别→状态的链路（4d 组另有真识别，但这几条是冗余的绿） |
| 14 | L955-971 滚轮/电池 | `S.scroll`/`S.batt` 打桩后 spot() 算术 | 真 wheel 事件在 scroll 模式下的 L5559 分支；`getBattery` |
| 15 | L1012-1020 笔倾斜 | `S.ptilt` 打桩 | L5512 `e.tiltX` 从 PointerEvent 进入的路径 |
| 16 | L1567 「切到非摄像头模态后摄像头已释放」 | 顺序 await 的 wM 会停轨道 | 并发调用时不释放（见 §2 B2，4 条 live track） |
| 17 | L1523-1531 fps | 本地 22/20；CI `e2e.yml` 降到 12/10 | 「全特效」没开 summon/offering/repel，这三者实测 6 fps（§3） |
| 18 | L885-887 视频坏 URL | `videoAttach` 设了 `S.video` 标志且 400ms 后仍 running | 404 的 error 事件 400ms 内未必到；证明的是 flag 不是容错 |

假测试比例估计：250 条里约 90–100 条属于「进入模态/数数/打桩/恒真」，≈ 38%（估计）。

## 2. 真 bug 狩猎（Playwright 实跑）

- **B1 严重 · 点完 42 张卡片 Chromium 渲染进程 SEGV**。`/tmp/adv/edge.js` 第一轮（每卡 25ms 连点两遍）在 ~5s 处 `Received signal 11 SEGV_MAPERR`，浏览器断连；`/tmp/adv/cards.js` 逐卡打印，第 35 张 `hid` 时 `BROWSER DISCONNECTED`。单独点 hid / midi→hid / ble / nfc / ir / osc→bridge→phone 都不崩（`/tmp/adv/hidtest.js` 8 组 crashed:false）→ 是累积效应，推测与 hand/face/motion/flashlight 连续重开摄像头 + MediaPipe WASM 重初始化有关。2/2 复现，一个真人顺着菜单点一遍就会掉页。二分未做完（未完成）。
- **B2 严重 · 摄像头泄漏（隐私）**。同步调用 `wM('hand');wM('face');wM('motion');wM('flashlight');wM('mouse')`，6s 后：`mode:"mouse", strNull:false, vidNull:false, gum:4, liveTracks:4, pip:"none"`（edge2.log §1b）。根因：`wM` L5189-5193 的 `initCam` 在 `S.mode!==name` 守卫之前就把全局 `str` 赋了值，而 `wM('mouse')` 早已跑过 L5184 的停轨分支。指针模式下摄像头灯常亮，PIP 还隐藏了，用户看不见。
- **B3 严重 · 一条坏载荷永久灭灯**。`extIngest({presence:'abc'})` → `clampN(NaN,0,1)`（L4166 两个比较都 false）返回 NaN → `S.bridge.presence=NaN` → `normSpot` 半径 NaN → 光圈不再绘制；之后 6 个用例（cmdPaint/xStr/arr…）全部 `presence:null, spotR:null`，直到有人重新发数值 presence。同理 `x:NaN` 使 `B.x=NaN`（§3 nan 用例 x/y/r/z 全 null）。`pushState` 还把 `presence:null` 回传给 ext-state（L3338），DMX `b()` 会把灯打到 0。
- **B4 严重 · server.py 可被单连接挂死**。`curl -m5 -H 'Content-Length: 60000' --data '{"a":1}' /send?room=osc` → `000 time=5.000616`：`rfile.read(n)` L250 永久阻塞，无 socket 超时，一个线程/连接，几十个这样的连接即可耗尽。同时 `room` 无长度/字符限制（5000 字符 room → 200），`_last[room]` L258 永不清理，随 room 名无限增长。
- **B5 严重 · 中继零鉴权 + 泄露令牌**。`/rooms` 列出所有 room（含手机配对 token）；`/send` 不要求 Content-Type、CORS `*`（L231/271），属于「简单请求」不走预检（OPTIONS 本身 501）→ 任何网页/局域网主机可向显示屏注入 scene/style/paint。跨源实测用例（edge2 §10）未完成，此条「推测」但依据是标准 CORS 规则 + 已观测的响应头。
- **B6 中 · `changeScene` 不校验参数**。`changeScene('3')` → `S.scene` 变成字符串；`99`/`-1`/`2.5`/`null` 全被接受，HUD 名空、下一场景算出 `3.5`，scene=99 时 fps 掉到 8（推测：drawScene 取不到图）。停卷（`S.running=false`）后调用仍改状态、弹场景导航，URL 却停留在 `?scene=0`（edge2 §2：`scene:4, url:"?mode=mouse&scene=0…"`）。
- **B7 中 · 窗口 resize / wall×50 / together 单指 / pushURL 计数**：脚本在 §3 之后随浏览器一起死亡，未完成。代码阅读：`wM` L5201 `replaceState('?mode='+name)` 会抹掉 `lang/stereo/accrete/grid/wall` 等参数，之后 `pushURL` L2223-2230 只回写 mode/scene/style/forms/delay → 换一次模态分享链接就丢参数（推测）。`pushURL` 节流 400ms，理论上 10s ≤25 次（推测，未计数）。
- **B8 中 · 共处 (together) 绕过**：L4746-4758 只把 `spots` 清空，但 `pushSplat`（空格/摇一摇）、`S.offering`、`S.paint` 留痕、`S.glow` 都不经 spots 门，单人仍能揭色（代码阅读，推测；实测未完成）。
- extIngest 其他输入：`scene:99`→1、`-1`→6、`NaN`→0、`"5"`→5、`1e308`→0、`style:"x"`→edges、`name` 1e6 字符→18、`id`→64、`state` 循环对象→接受且不抛（因为 pushState 不序列化 state）。无抛错，但 `-5` 负数 r 被夹到 0.02 → 半径 8.8px 几乎不可见，且不提示。

## 3. 内存 / 性能（`/tmp/adv/mem.log`）

- 60s mouse：afterGC 2.1MB 恒定（fps 90–120）；60s 点云：2.7MB 恒定（fps 25–42）；30s paint+glow+summon+offering(12)：2.7MB 恒定但 **fps=6**。无堆泄漏，DOM 988 节点不变。
- 每帧分配：`processFrame` 本体 282 行（L4728-5009）无 `createElement('canvas')`；但 summon L4807、offering L4822 每点每帧 `createRadialGradient` + 各自整幅 `drawImage(scCvs)` 三趟，是 6 fps 的来源。`changeScene` L4707 每次新建整幅 canvas，OSC/桥 `scene` 洪泛即每条消息 5MB 分配。`glowSprite` 缓存 L4352 以 hue 为键无上限，inkpick 的任意 hex（L4094）会一直攒（推测）。

## 4. 安全（curl 实打，`http://127.0.0.1:8930`）

- 路径遍历：`--path-as-is` 的 `/../server.py`、`/..%2f`、`/%2e%2e/`、`/scenes/../../` 全 404 ✔。`/scenes/` 目录列表 200（信息泄露，低）。
- 超大 body 70000 → 400 ✔；`Content-Length` 大于实际 → 挂死（B4）；chunked → 400。
- 非 JSON → 400 ✔；但 `[1,2,3]`、`42`、`"str"` → 200 delivered 1（非对象照样广播）；`1e400` → Python 解析成 inf，`/state?room=osc` 回 `"y": Infinity`，不是合法 JSON（实测）。
- `room=a%0d%0ab`、5000 字符 room → 200（B4）；`/state?room=osc` 无鉴权读到最后一条载荷；`/osc` 接受 `{"scene":"<script>"}` 原样存入。
- body 里的 `\r`：server L261 只替换 `\n`，`{"x":0.22,\r"y":0.22}` 200 delivered 1；`\r` 是 SSE 行终止符，客户端会收到被拆开的事件（客户端效果未实测，推测）。
- `SECURITY.md` 第 7 行写「没有服务器、零后端、数据从不离开设备」，而 server.py 存在且页面每 500ms 把状态 POST 出去（L3341）。文档不实。

## 5. 记分卡作弊面（`score.mjs`）

1. `coreMechanic` L111：只 grep 字符串 `光圈内的颜色与圈外不同` 是否在 test.js 里 → 写一行注释即 100%。
2. `modeCoverage` L107：`testSrc.includes("'"+k+"'")` → 一个列出 42 个名字的数组字面量即 100%（现在的 L468 数组就是这样算进去的）。
3. `e2e` L29-31：直接信任 `tools/last-run.json`，不带 `--run` 时手写 `{"pass":250,"fail":0}` 即满分；且 `ok(…, true)` 这类恒真也计入 pass。
4. `degradation` L74-79：在模态对象里写 `fallback:'none'` 即免检；或源码任意处出现 `|| null` 也算「有失败路径」。
5. `a11y` L100-102：只查 5 个字符串是否出现在 HTML 文本里（注释里也算）。

## 6. 结论

严重（5）：B1 42 卡连点浏览器 SEGV；B2 并发 wM 摄像头泄漏；B3 NaN presence 永久灭灯；B4 Content-Length 挂死 + room 无限增长；B5 中继零鉴权、/rooms 泄露配对 token。
中（4）：B6 changeScene 不校验/停卷后 URL 不一致；B7 wM 抹掉 URL 参数（推测）；B8 together 可被 splat/offering/paint 绕过（推测）；summon+offering 6 fps（实测）。
低（4）：/scenes/ 目录列表；非对象 JSON 与 Infinity 进入 /state；SECURITY.md 与现实不符；e2e.yml 写 95 条、score.mjs 写 141 条、REVIEW 写 250 条（违反其自定规则 7）。
未完成：脏 URL、resize、wall×50、together 触摸实测、pushURL 计数、跨源劫持实测。

**250 条绿断言真正能证明的是：** 42 个名字能被写进 `S.mode`、几十个纯函数的算术正确、以及 3 条真识别在一张固定照片上过了；它们不证明任何一条输入→光圈链路在并发、坏数据或真人乱点下还活着。
