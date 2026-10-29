# 变更记录 · Changelog

遵循 [SemVer](https://semver.org/lang/zh-CN/)。每个版本都对应一组 CI 绿了的提交。

## [0.2.7] — 2026-10-29

**六份评审留下的工程项，全部做完**

### 契约（通用框架的根因）
- `Spot` 新增 `t`（时间戳）、`vel`（像素/秒，跨帧平滑）、`members`；`extent` 类型化孔径 `disc | band | rect | brush`
- 内容源可用 `extent(spot,W,H)` 决定孔径：文本源变成「一列」，照到哪一列读哪一列
- 书写形式的笔宽真的进渲染（之前算了没用）

### 形式的可见签名
- 延迟虚线环、共处人数格、仪式墨点 + 倒计时、静默进度弧、日课朱印、驱赶外推刺；每种开 / 关像素差断言

### 离线与展厅
- MediaPipe 本地优先：`python3 tools/vendor_mediapipe.py` 下载约 34 MB 到 `web/vendor/`，启动时 HEAD 一次，有就不碰 CDN；实测 CDN 全被拦 0.4 s 起页
- `examples/kiosk/`：Linux/macOS 启动守护脚本、systemd 单元、Windows bat、`watchdog.py`
- 投影墙模式每 5 s 向 `room=heartbeat` 报 fps；`GET /health` 返回 `heartbeat.alive`
- 点云漂移相位按墙钟（`S.clock0`），两台机器各自开页也同相
- NDI / Spout：经 OBS 浏览器源的接法写进 `docs/CREATIVE-TOOLS.md`

### 健壮性
- `wM` 串行化 + 合并：连点 42 张卡片不再各自开摄像头 / 初始化模型（之前渲染进程 SEGV）；摄像头按朝向复用
- 14 个模态补上 `fallback` 声明；`spF(null)` 不再抛

### 测试诚实度
- 「可进入」类断言改为行为断言：spot 输出必须是画布内有限数、`ex()` 不抛、声明了降级；NFC 验 `scan()` 真被调用且读「雪」换画；环境光验降级到指针；点云「光位改变视角」改为同一时刻定住漂移的确定性对比；首屏时间断言不再恒真；删一条重复计数
- 断言 273 → **289**；创作软件自检 11 → 13

## [0.2.6] — 2026-10-29

**内容源接口：隐藏层不再只是那 5 张图**

### 新增
- `registerSource / useSource`：任何实现 `drawColor(g,W,H,t)` 的对象都能当隐藏层；可选 `drawMask / live / overlay / rawMask`
- **上传**：拖图 / 视频进页面、首页「上传你的画」、按 `U`、`?img=<url>`；内容不离开浏览器
- **文本源**：`?story=1` 内置《桃花源记》开篇（公有领域），竖排右起；墨层只画纸与行栏，**字要被光照到才显**；`?story=<txt>` 换任何文本
- **声音层**：`?sound=demo|<url>`；光越大低通越亮、x 决定声像、在场度决定响度、无光静音
- **视频活墨层**：`?livemask=1` 墨层每 400 ms 跟随视频，不再只取首帧
- `window.InkScroll` 新增 `registerSource / useSource / image / video / story / sound / soundOff / sources`
- `docs/SOURCES.md`

### 修复
- 首页「展厅模式」按钮从未绑定事件（死按钮）

### 测试
- 断言 263 → **273**（注册 / 活墨层 / 文本 / 拖放上传 / 声音参数与节点 / API / 展厅按钮）

## [0.2.5] — 2026-10-29

**六份独立评审后的修复批次**（`docs/reviews/`）

### 修复（用户可感）
- **42 张模态卡片里 22 张永远不可见**：淡入动画只给了每组前 6 张，其余停在 opacity 0。现在每张都淡入
- **供奉 / 仪式 / 召唤真实点击不触发**：判断写在 `pointermove` 里却检查 `pointerdown`，搬进正确的监听器
- `?preset=kiosk` 的 `mode:'auto'` 从未生效（被默认模式覆盖）
- 首页标语渲染两遍；CTA 行压在卡片上 → 全宽渐隐条
- 投影墙模式会把入场引导卡弹到墙上；校准网格的画框 / 字母 / 分辨率是纸色画在纸色上
- `?stereo=sbs` 的墨层仍是单目整幅，双机立体对不上
- 4K 投影机：`computeDPR` 下限钉死 1，像素预算不生效 → 允许 <1
- 入场引导在桌面上一次都看不到（鼠标一动就关）→ 移动超过 60px 或点击才关
- MediaPipe 脚本同步阻塞 `<head>`，CDN 黑洞时页面 45 秒起不来 → `async` + 手势模态等模型就绪；Google Fonts 改为不阻塞渲染

### 修复（健壮性 / 安全）
- 并发切换摄像头模态会留下多条活着的轨道 → `initCam` 丢弃孤儿流
- `extIngest` 收到非数字 / 循环对象会让光圈半径变 NaN 永久消失 → 逐字段过滤
- `server.py`：假 `Content-Length` 永久挂死 → 5 秒超时；room 名长度 / 数量上限；`/rooms` 不再泄露手机配对 token；可选 `INK_TOKEN` 鉴权

### 可及性 / 伦理
- 换场景进 `aria-live` 播报；重建卡片后焦点回到当前模态
- 第一次进摄像头 / 麦克风模态时界面内显示「只在本机换算、不录制不上传」
- `og:image` 改绝对路径 + `twitter:card`；英文 / 繁体 README 从 21 模态更新到 42

### 文档
- `docs/reviews/`：策展人 / 跨媒介艺术家小组 / creative technologist / 增长 / 教育无障碍 / 严苛审查 六份原始报告 + 合成结论

### 测试
- 断言 250 → **263**（评审回归 12 条 + 脏载荷 / 轨道泄漏 2 条，去掉 1 条已不适用）

## [0.2.4] — 2026-10-26

### 新增
- **11 种交互形式**（原 7 种 + 驱赶 / 召唤 / 书写 / 仪式），全部进帮助面板
- **入场三步引导**：首访出现，4.5 秒或首次交互消失，localStorage 记住
- **场景缩略图**：6px 圆点 → 26×18 真实小图
- **状态进 URL**：`?mode=&scene=&style=&form(s)=&delay=` 一键分享整套配置
- `docs/REVIEW.md`：10 条代码审核清单 + 每次审核记录（含 CI 连红的复盘）

### 修复
- 首帧崩溃（形式层状态字段没插进 `S{}`）
- 默认模式误判为 multi（COARSE ≠ 多点触控）
- `changeScene` 早期调用（画布未建好）导致 drawImage 类型错误
- `applyPreset` 在 `wall:false` 时没移除 `body.wall`
- 三语 304 键双向对齐

### 测试
- 断言 166 → **250**；创作软件自检 11 条（OSC / Art-Net / MQTT payload / Blender）

## [0.2.3] — 2026-10-21

### 新增
- **42 个模态**：+ 笔倾斜 / 房间底噪 / 节拍 BPM / 天时 / 剪贴板 / 取色 / 在场 / 多屏 / 展厅锁键 / 机器负载 / 口哨 / 滚轮 / 电池
- **契约 `Spot{id, presence, state}`**：多人与传感器融合有了地方落
- **双向通道**：页面 → 脚本 `room=ext-state`（500ms 状态回传）
- **Art-Net DMX**：CH1 亮度 / CH2 x / CH3 y / CH4 半径，真灯跟着光圈走
- **预设** `?preset=gallery|kiosk|stereo|lab` + `docs/PRESETS.md`
- **图谱** `docs/MODALITY-ATLAS.md`：125 条模态 / 12 类传感器

## [0.2.2] — 2026-10-21

### 新增
- **吹墨** `blow`（第 42 个模态）：吹气 → 墨层像灰尘散去 → 露彩色，停吹回墨
- **3D 耦合**：声音（响度→仰角/张开、音高→雾）、呼吸（→雾浓度）、捏合（→抓住画卷推拉）
- **点云视角**：滚轮推拉 / 双击定住 / Shift+拖绕轴
- `docs/IDEAS.md`：20 条可落地的脑洞 + 5 条明确不做 + 4 条待验证假设

## [0.2.1] — 2026-10-21

**3D 一层**

### 新增
- **第 7 张场景「立轴 · 点云」**：亮度当深度，自写 canvas 2D 透视投影 + 雾化，零新依赖
- **深度进契约** `{x,y,z,r}`：OSC `/spot x y z r`、`bridge`、`postMessage` 三处入口
- **头部视差**：FaceMesh 鼻尖 z 进点云 dolly（复用已有模型，0 字节）
- **投影墙** `?wall=1` + 校准网格（A/B/C/D、三分线、中心十字、分辨率标注）
- **立体输出** `?stereo=anaglyph|sbs`
- `docs/VISION-3D.md`：3D 路线 + 需求实证（MCT LB/T 097-2025、¥119.78 万采购、BLINK 944 投稿）

### 变更
- 断言 146 → **166**；模态 29 → **30**；场景 6 → **7**
- 记分卡 `degradation` 维度支持**显式 `fallback` 声明**，不再只靠正则猜测

## [0.2.0] — 2026-10-21

**从「能跑」到「有标准」**

### 新增
- **42 种交互模态**，分四档：13 免外设 / 5 只用摄像头 / 9 插装置 / 2 本机脚本
- 免外设新增：多指多灯、键盘、压感笔锋、凝视停留、吐纳、拍手、语音、摇一摇、环境光
- 摄影头新增：面庞头姿、眨眼（EAR）
- 装置新增：手柄、MIDI、HID（Joy-Con/Wiimote）、蓝牙（心率/EEG）、NFC
- **创作软件接入**：`window.InkScroll` + `postMessage`；OSC `udp/9000`；`POST /send?room=ext`
- Blender 适配器（真机 4.2.3 验过）、TouchDesigner 配方（OSC 报文 7/7 验过）
- 内容层：程序化 3D 视差立轴（第 6 张）、视频层 `?video=`
- 手机众光：`server.py`（零依赖 SSE 中继）+ `web/phone.html`
- 控制栏 / 帮助面板 / 深链 `?mode=&scene=&style=&lang=` / 分享卡

### 变更
- 默认风格改为**纸本**（墨落宣纸），暗房光束保留为「墨线」
- 场景图改为真 JPEG、`cover` 全幅出血、预缩放缓存
- 画布 DPR 感知（上限 2×，受 3.2 MP 预算约束）

### 修复
- 默认模态为 `phone` 导致首屏被遮罩堵死（改为指针/多指/自动按设备挑）
- 离开摄像头模态不释放摄像头（隐私）
- 切进「外设桥」会复位刚收到的坐标
- MediaPipe `hands` / `face_mesh` 共享全局 `locateFile` 造成跨目录 404
- 手机页权限请求遮住整页操作

## [0.1.0] — 2026-09

初始原型：手电筒 / 手势 / 眼动（ArUco）/ 鼠标 四种模态，5 张场景，3 种风格。
