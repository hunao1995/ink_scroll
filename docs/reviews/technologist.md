# 墨卷 · Ink Scroll — Creative Technologist 评审（能不能进场地跑一个月）

评审人视角：做过商业投影装置，日常用 TouchDesigner / Resolume / Unreal。
环境：仓库只读；`server.py` 跑在 8930；Playwright + 本机 chromium（**SwiftShader 软件渲染**，HD 数字偏保守，4K 的结论是结构性的，见下）。日期 2026-10-29。

## 1. 架构判断

- **形态**：`web/index.html` 单文件 5814 行（Canvas 2D，无 WebGL），+ `server.py` 327 行 stdlib 中继（静态文件 / SSE 房间 / UDP 9000 OSC / Art-Net 出）。
- **场地里的优点**：零安装、零依赖、任何能开 Chromium 的盒子都能跑；OSC → SSE 这条链路实测很短（见 §2）；`processFrame` 每帧 try/catch（`index.html:4730`/`5007`），一帧抛错不会黑屏；EventSource 自带重连，中继重启页面不用动；`/health` 能接监控。
- **场地里的缺点**：所有合成在 Canvas 2D 主线程，`processFrame` 每盏光都整幅 `drawImage(scCvs)`（`index.html:4859`），分辨率一上去就线性崩（§2 的 4K 数据）；没有输出通道（无 NDI/Spout），意味着**几何校正、融合、色彩只能靠「把浏览器窗口丢给另一台机器抓」**；中继 0.0.0.0 无鉴权；kiosk 守护（崩溃重启、黑屏检测）完全没有。
- **与 TD / Unreal 的位置**：它不是 TD 的替代品，是一个「内容节点 + 交互逻辑」。TD/Unreal 做同样的事（光圈揭示隐藏层）一个下午就能搭出来，而且天然有 Spout/NDI、warp/blend、时间线。墨卷的真正价值是 42 个模态和手机众光这套交互 + 「不装软件就能开」；进场地的正确姿势是**浏览器当内容源，TD/MadMapper 当输出层**，而不是让浏览器直出投影机。

## 2. 实测（贴数字）

| 项目 | 视口 | 结果 |
|---|---|---|
| 纸本（scene 0, paper） | 1920×1080 | 47–60 fps，heap 3 MB |
| 点云（scene 6） | 1920×1080 | 28–37 fps |
| `?preset=kiosk`（点云 + 网格 + wall） | 1920×1080 | 40–43 fps，自动开卷 ~1.5 s，无需点击 |
| `?preset=stereo`（sbs，点云画两遍） | 1920×1080 | 15–25 fps |
| `?wall=1&grid=1`（纸本） | 1920×1080 | 54–62 fps |
| 纸本 | **3840×2160, DPR 1** | **5–7 fps**，`S.dpr=1, DW=3840, DH=2160` |
| 点云 | 3840×2160 | 4–7 fps |
| kiosk | 3840×2160, deviceScaleFactor 2 | 5–9 fps，`S.dpr` 仍 = 1 |
| 运行中 HD→4K 热切换（投影机 EDID 变化） | — | DPR 不变，画布直接变 8.3 MP，9 fps |

- **DPR 结论**：`computeDPR`（`index.html:5099`）是 `max(1, min(2, raw, sqrt(3.2M/area)))`，下限钉死在 1，所以 3.2 MP 预算对 4K 投影机（DPR=1 的机器）完全不生效，注释里说的「不让 4K 变成 33 MP blit」只对 retina 成立。软件渲染数字会比真 GPU 差，但 8.3 MP 画布每帧 3–6 次整幅 drawImage 的量级在任何集显上都不会到 60。
- **OSC 往返**（`/spot` UDP → `/events?room=osc` SSE，本机）：50 条单发 **中位 0.99 ms，p95 4.6 ms，max 20.5 ms**；300 条 @60 fps 突发 **300/300 收到**；2000 条无间隔洪水收到 749（队列 maxsize 200，按设计丢）；HTTP `POST /send` → SSE 中位 2.7 ms。垃圾包 / 空包后 `/health` 仍 ok。
- **`python3 tools/check_integrations.py`**：**11 passed / 0 failed / 0 skipped**（OSC 3 条、API 3 条、Art-Net 3 条、Blender 无头 2 条）。
- **投影墙 UI 残留**：wall 模式下 `#ui #bar .scene-nav #first-hint .credit #roster #gh #glegend .lang-switch` 都隐藏、cursor none，截图干净；**但 `#onboard` 不在隐藏列表**（CSS `index.html:673-676`），kiosk 开卷 0.9 s 后弹出「移动光标…」引导卡 4.5 s（实测 t=3 s、6 s 均可见）。它靠 localStorage 记住，kiosk 若用 `--incognito` 或每天清 profile 就**每次开机都弹到墙上**。
- **校准网格**：三分线（赭色）可见；画框、中心十字、A/B/C/D、分辨率文字用 `rgba(245,244,237,.92)`（`index.html:4946-4958`），画在 `#f5f4ed` 纸色隐藏层上——**kiosk 默认配置里全部看不见**（截图确认）。网格字体还用 Google Fonts 的 Noto Serif SC。
- **stereo 预设**：`genHidden` 的点云分支（`index.html:2610`）不看 `S.stereo`，隐藏层是一整幅单目点云；只有光圈内的彩色层是 SBS。双机投影时两台机各拿到半幅单目图 + 光圈里才有立体对，截图确认（光圈落在右半幅空白区）。
- **3 分钟 soak**（kiosk + OSC 20 Hz + 每 10 s 换场景）：JS heap 2–5 MB 平稳，listeners 恒 161，DOM 节点 1.5k–5k 波动不单调增长，0 pageerror。一个月量级 **未核实**。

## 3. 进场地会炸的地方（按严重度）

1. **断网 / 受限网络 → 页面永远起不来**。`<head>` 里同步 `<script src="https://cdn.jsdelivr.net/npm/@mediapipe/...">`（`index.html:1049-1050`）。实测：CDN 请求被 abort 时 0.7 s 可开；**CDN 黑洞（连上但不响应，场地 captive portal / 防火墙的典型表现）时 DOMContentLoaded 45 s 内都没到**。Google Fonts（`index.html:13-15`）大陆直连不可用，字体回退不会崩但同样会拖 onload。复现：Playwright `route(/jsdelivr|googleapis/, r=>{})` 不 fulfil。
2. **4K 投影机不可用**（§2）。1080p 还行，4K/双 4K 直接个位数帧。复现：视口 3840×2160 读 `S.dpr` 与 `S.fps`。
3. **中继无鉴权且监听 0.0.0.0，CORS `*`**（`server.py:231,271,309`）。场地 Wi-Fi 上任何人 `POST /send?room=ext` 就能换场景、泼墨、劫持 `ext-state` 驱动 Art-Net 灯；手机 room token 可猜。实测未带任何凭据的 POST 返回 `{"ok":true}`。
4. **没有 kiosk 守护**。无 systemd / Task Scheduler 示例，无崩溃重启，无黑屏/卡帧 watchdog（页面有 `S.fps` 但没有上报；`/health` 只知道有几个 SSE 客户端，不知道画面有没有在动）。Chromium `--kiosk` 崩掉后就是桌面；`navigator.keyboard.lock` 只锁 Esc/Q/Tab/F11，Alt+F4 / Win 键不锁。**未核实**真机重启行为。
5. **stereo 隐藏层非 SBS**（§2）——双机立体方案现在是坏的。
6. **kiosk 墙上会弹引导卡 + 网格标注不可见**（§2）。两处都是一行 CSS / 一个颜色值。
7. **无色彩管理 / 无黑电平**。Canvas 默认 sRGB，源码无 `colorSpace`/gamma/亮度控制；纸色 `#f5f4ed` 投到白墙是一大块亮灰，投影机黑不是黑，「纸本」风格在投影上会失去对比。只能靠输出层（TD/MadMapper）补。
8. **无多投影融合 / warp**，文档已自认（PRESETS.md §kiosk）。没有输出通道的话等于「必须再加一台抓屏机」。
9. **长时间运行**：3 分钟 soak 干净；`pushURL` 每 400 ms `history.replaceState`、`pushState` 每 500 ms POST，量级安全。`sceneCache` 按场景索引缓存全幅 canvas（7 幅 × 8.3 MP × 4B ≈ 230 MB 显存 @4K）**未核实**是否触发 GPU 回收。
10. 小错：`server.py` 文档字符串 `/scene i → 0..4`，实际 `SCENE_COUNT=7`；`/spot f f f` 第三个是 r 不是 z（和 TD 文档一致，但和 docstring 的 `z` 冲突）。

## 4. 要进 TD / Unreal 工作流还缺什么（优先级）

- **P0 输出通道**：无 NDI / Spout / Syphon。浏览器做不到 Spout；现实解法是 OBS Browser Source → NDI/Spout（今天就能做，零代码，但多一跳 1–2 帧延迟）或 Electron + spout 插件。没这一条，warp/blend/色彩全部无从谈起。
- **P1 视频输入**：只有 `?video=<url>` 文件；没有 NDI in / WebRTC in，TD 生成的纹理进不来。
- **P1 多机同步**：无帧锁、无时钟。点云漂移 `Math.sin(t*0.24)` 用各机本地时钟，双机立体会慢慢错相；`S.screens` 只覆盖单机多屏。
- **P1 时间码 / show control**：无 LTC/MTC，无 `/play /pause /cue /blackout` 一类 OSC 地址（只有 `/spot /scene /style`）。一个月的展最少需要定时开关与一键黑场。
- **P2 OSC out**：页面状态只走 SSE `ext-state`；TD 想读要再写一个 SSE 客户端。`server.py` 加 OSC 回发 20 行。
- **P2 DMX**：只有 Art-Net 单 universe 4 通道，无 sACN，无 DMX-in（控台无法反向切场景）。
- **P3** Ableton Link、MIDI clock、远程配置 API（现在靠 URL 参数）。

## 5. 框架迁移：`drawScene` / `genHidden` 管线要改哪里

现状：`drawScene(t)`（`index.html:2415`）每帧把彩色层画进 `scCvs`，分支 video / 3D / cloud / 静态图；`genHidden()`（`:2591`）只在换场景、resize 时跑一次：在 ≤1.25 MP（`MASK_BUDGET`）的离屏画布重画同一内容，然后 CPU `getImageData` + sobel/sketch/paper/dark 生成墨层 `hiCvs`。两者**没有共享的「内容源」抽象**，每加一种内容要在两个函数各加一个 `if`。

| 隐藏层换成 | 改哪里 | 难度 |
|---|---|---|
| 视频（墨层跟随每帧） | 现在墨层只取首帧（`:2604-2606`）；要每帧重跑 sobel 1.25 MP CPU（~20–40 ms），必须把滤镜搬到 WebGL/WebGPU shader 或 OffscreenCanvas worker，再让 `processFrame` 用纹理合成 | **M** |
| 3D 场景（three.js / WebGL） | 彩色层 `drawImage(glCanvas)` 可直接塞进 `drawScene`；墨层若要跟着视角动，同上需要 GPU 边缘滤镜，否则只能做静态墨层 | **M** |
| 实时生成图像（SD 流 / TD 纹理） | 没有任何 ingest（无 WebRTC/MJPEG/NDI），先补输入通道，再按「视频」处理；延迟与分辨率还会反过来逼 Canvas 2D 合成换成 WebGL | **L** |
| 音频可视化 | `S.audio` 分析链已在（`audioLoop`），只需在 `drawScene` 加一个分支画频谱/波形，`genHidden` 可节流到 10 Hz 或直接复用彩色层做墨层 | **S** |

共同前提：先把「内容源」抽成 `{drawColor(ctx,W,H,t), drawMask(ctx,w,h,t), dirty}` 接口，两处 `if` 链各改成一次调用，否则每加一种都要改两处。

## 6. 三条最该先修的

1. **离线可启动**：MediaPipe / 字体本地化并改 `defer` 或按模态懒加载；加 `route` 黑洞测试进 `tools/test.js`。**0.5 天**。
2. **4K / DPR**：`computeDPR` 允许 <1（按 3.2 MP 预算缩画布，CSS 放大），顺手让 resize 热切换也走预算；长期把合成搬到 WebGL（3–5 天）。**短修 0.5 天**。
3. **锁中继 + kiosk 硬化**：`INK_TOKEN` 校验 `/send` `/osc`，默认绑 127.0.0.1 或白名单；wall 隐藏 `#onboard`；网格描边改深色；给一份 systemd/Task Scheduler + `--kiosk --incognito --disable-session-crashed-bubble` 启动脚本和 `S.fps` 上报到 `/health`。**1 天**。

## 摘要

- **场地可用性：4 / 10**（1080p、有网、单机、局域网可信时能跑；一个月无人值守、4K、双机立体、受限网络下现在不行）。修完上面三条约 **7 / 10**。
- **最大风险**：`<head>` 同步拉 CDN——场地网络一旦黑洞，墙上永远是空白页；其次是 4K 下 5–9 fps 与无鉴权中继。
- **修法 1**：MediaPipe/字体本地化 + 懒加载，离线起页 <2 s（0.5 天）。
- **修法 2**：`computeDPR` 下限放开到 <1，按 3.2 MP 预算渲染（0.5 天）；中期 WebGL 合成。
- **修法 3**：中继加 token + 默认绑本机，wall 隐藏 `#onboard`、网格改深色、补 kiosk 启动/重启脚本（1 天）。
- 未核实：一个月级内存/显存、真机 GPU 帧率、Google Fonts 大陆实际行为、Chromium 崩溃重启。
