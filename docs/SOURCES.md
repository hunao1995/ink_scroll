# 内容源 · Sources

> 六份评审里一个共同判断是：这套框架的揭示层「只认像素」。这一页说清它现在认什么、怎么把任何内容接进来。

## 一句话

**光揭开的不一定是一幅画。** 只要一种内容能画到画布上，它就能被光揭开：图片、视频、3D、点云、文字、生成图形。
声音走另一条线：光不揭开画面，而是揭开声音（滤波 / 声像 / 响度）。

## 内置的内容源

| 内容 | 入口 | 墨层怎么来 |
|---|---|---|
| 5 张水墨（测试素材，AI 生成） | 默认 · `?scene=0..4` | 从画里算（Sobel / 素描 / 纸本 / 暗调） |
| 3D 视差立轴 | `?scene=5` | 同上 |
| 点云 | `?scene=6` | 点阵本身就是墨 |
| **你自己的图** | 拖进页面 · 首页「上传你的画」· 按 `U` · `?img=<url>` | 从图里算 |
| **你自己的视频** | 拖进页面 · `?video=<url>` | 默认取首帧；`?livemask=1` 每 400 ms 跟随 |
| **文本（历史故事）** | `?story=1`（内置《桃花源记》开篇，公有领域）· `?story=<txt url>` | 墨层只画纸与行栏：**字要被光照到才显** |
| **声音层** | `?sound=demo`（五声 drone）· `?sound=<audio url>` | 光越大低通越亮；x 决定声像；在场度决定响度；无光静音 |

上传的内容不离开你的浏览器（`URL.createObjectURL`，没有任何上传路径，见 `docs/ETHICS.md`）。

## 接口

```js
// 任何实现了 drawColor 的对象都是一个内容源
InkScroll.registerSource('mine', {
  name: '我的内容',
  live: false,          // true = 每 400ms 重算墨层（视频 / 生成内容）
  overlay: false,       // true = 叠水墨粒子氛围
  rawMask: false,       // true = 墨层不走风格滤镜
  drawColor(g, W, H, t){ /* 画被光揭开后看到的东西 */ },
  drawMask(g, w, h, t){ /* 可选：画给墨层用的底图；想藏住内容就在这里画空白 */ },
  init(){}, cln(){}     // 可选
});
InkScroll.useSource('mine');     // 启用
InkScroll.useSource(null);       // 回到 7 张场景

InkScroll.image(url, name);      // 远程图（需 CORS）
InkScroll.video(url);            // 视频 + 活墨层
InkScroll.story(text, title, author);   // 竖排文本
InkScroll.sound(url);            // 声音层；InkScroll.soundOff()
InkScroll.sources;               // 已注册的 id 列表
```

## 什么能搬、什么不能（诚实版）

| 层 | 媒介无关 | 说明 |
|---|---|---|
| 输入（42 模态、中继、OSC/HTTP/MQTT） | ✅ | 和内容无关 |
| 形式（延迟 / 共处 / 仪式 / 静默 / 累积 …） | ✅ | 只改光点数组，不碰内容 |
| **内容源** | ✅（本版新增） | 任何能画到 2D 画布的东西；声音走参数映射 |
| 揭示几何 | ⚠️ | 仍是「圆 / 椭圆局部裁剪」。阅读顺序（诗）、笔势（书法）、身体线（舞蹈）需要把 `radius` 换成类型化 `extent`，还没做 |
| 水墨质感（Sobel 墨线、粒子、题款） | 水墨专属 | 换内容时可用 `rawMask` / `overlay:false` 关掉 |

所以准确的说法是：**输入层、形式层、内容层都通用；揭示几何还是一个圆。** 下一层要动的是 `Spot{x,y,radius}` 本身。

## 给策展人 / 合作者

- 不想要熊猫：`?img=https://你的图` 或直接把画拖进页面，30 秒内换成你的作品。
- 文物 / 文献：`?story=<txt>`，第一行当标题，其余正文，竖排右起。
- 配乐：`?sound=<mp3>`，光就是混音台。
- 这些都能和 11 种形式叠加：`?story=1&form=together&delay=8000`。
