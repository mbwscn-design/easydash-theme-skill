# EasyDash 主题格式速查

## 从一张能读数的卡片开始

下面是一份完整的无素材 `manifest.json`。它在 960 × 540 横屏画布上显示电压，接收车辆的实际采样，保留一位小数。编辑器用模拟值预览。

```json
{
  "schemaVersion": 1,
  "id": "pitlane-voltage",
  "title": "维修区电压表",
  "orientation": "landscape",
  "backgroundColor": "#101719",
  "canvas": {"width": 960, "height": 540, "fit": "contain"},
  "elements": [
    {
      "type": "metric", "gaugeStyle": "nameplate",
      "x": 40, "y": 40, "width": 480, "height": 210,
      "parameter": "battery_voltage", "slot": "electrical", "slotLabel": "电压",
      "label": "电压", "unit": "V", "decimals": 1,
      "autoLabel": true, "autoUnit": true,
      "color": "#63D3CB", "labelColor": "#B6C7CA", "backgroundColor": "#172527"
    }
  ]
}
```

主题 `id` 建议使用简短英文标识，首字符为字母或数字，可包含下划线、点和连字符，最多 128 字符，避免连续两个点。标题最多 120 字符。`orientation` 可取 `landscape` 或 `portrait`。`canvas.fit: "contain"` 保持宽高比并显示完整画布，`cover` 可能裁边，`fill` 会拉伸。可选的 `preview` 对象使用 `text`、`color`、`backgroundColor`、`borderColor` 指定封面标记。颜色采用 `#RRGGBB` 或 `#AARRGGBB`。

元素必须有数字坐标 `x`、`y` 和正数尺寸 `width`、`height`。数组顺序从背景到前景。可选 `rotation` 以中心为轴，正数顺时针。画布每边最多 8192，总面积最多 33,554,432 个逻辑像素。可导出的主题包含 1 至 128 个组件。

## 可选组件与外观

新样式填写在组件自己的 `gaugeStyle`。省略它或设为 `standard`，按组件原有配置绘制。导入旧主题时，保留作者已有的颜色、`layout`、`displayStyle` 和数据槽。支持该组件类型、尚未支持新 `gaugeStyle` 的客户端通常沿用原有外观。需要展示特定效果时，用目标客户端实际预览。

| `type` | 用途 | 可选 `gaugeStyle` 或主要字段 |
| --- | --- | --- |
| `metric` | 车速、档位、电压等读数 | `timing` 计时数字、`scanline` 扫描数字、`sideBand` 侧标卡、`nameplate` 铭牌卡 |
| `arcGauge` | 连续变化的弧形读数 | `segmented` 分段环、`minimal` 细环、`trackArc` 赛道粗弧、`blockArc` 断块环。`showValue: true` 打开中心读数 |
| `radialGauge` | 指针表、多指针表 | `classic` 机械盘、`minimal` 简刻盘。`showNeedle`、`majorTicks`、`minorTicks`、`showTickLabels` 控制指针与刻度 |
| `barGauge` | 温度、转速或百分比进度条 | `solid` 连续条、`graduated` 阶梯条、`blockCells` 方格条、`dotMatrix` 点阵条。`layout: "vertical"` 自下向上，`segments` 设置分段，`dotColumns` 和 `dotRows` 设置点阵 |
| `vehicleDiagram` | 车身轮廓及最多四个通道 | `outline` 线框、`compact` 数据列表。`parameters`、`slots`、`slotLabels`、`labels`、`units`、`decimalPlaces` 按通道排列并对齐 |
| `traceChart` | 遥测历史曲线 | 用 `series` 数组指定每条线的 `parameter`、`label`、`color`、`slot`、`slotLabel`。实时曲线取实际历史采样 |
| `image`、`rpmImage` | 背景、插画、随转速切图 | 见下方图片和音效章节 |
| `label`、`panel`、`line` | 静态标题、面板和分隔 | `label.text` 为静态文案。变化的读数用 `metric`。格式也接受 `grid`，目前绘制器会隐藏它，需要可见网格时用局部细线或背景图 |

仪表 `min`、`max` 使用通道原始单位，`max` 必须大于 `min`。环形起点和跨度可用 `startDegrees: 135`、`sweepDegrees: 270`。`color` 控制进度或数值，`trackColor` 控制底轨。数值卡的 `format` 可取 `number`、`gear` 或 `timer`。档位 0 显示 N、负数显示 R。计时输入为秒，显示分钟和秒。常用小数位为 0 至 3，普通数值格式最多显示 3 位。无有效数值时，普通读数显示 `--`。

数值卡可选 `valueScale` 和 `valueOffset`，显示值等于采样值 × 系数 + 偏移。只修改 `unit` 会替换单位文字。可用 `alarmEnabled: true` 配合 `highThreshold`、`dangerThreshold` 或 `lowThreshold` 着色，这些阈值比对原始采样。根据车型或用户要求选择阈值。

## 车辆通道与版本更新

`parameter` 决定默认数据来源，`slot` 标记仪表中可被用户重新绑定的位置，`slotLabel` 是选择通道时显示的名称。一个转速数字和一个转速环可共用 `slot: "engine_speed"` 并指向同一默认通道。若需要能分别换绑，则使用两个槽。多指针表的 `series` 每项可各有 `slot`、`slotLabel`。改主题外观或提交新版时，保留作品原有 `id` 和仍表达同一用途的槽名，新增用途使用新槽名。市场版本应在同一作品下提交新版。

| 读数 | 可用的参数 ID | 原始单位 |
| --- | --- | --- |
| 车速、转速 | `speed`、`rpm` | km/h、RPM |
| 水温、进气温度、机油温度 | `coolant_temp_std`、`intake_temp_std`、`oil_temp_std` | °C |
| 电压 | `battery_voltage` | V |
| 节气门开度、发动机负荷 | `throttle_std`、`engine_load_std` | % |
| 进气歧管绝对压力、空气流量 | `turbo_std`、`maf_std` | kPa、g/s |
| 发动机运行时长 | `run_time_std` | s |
| 厂家档位、机油温度、变速箱油温示例 | `gear_lufi1`、`oil_temp_lufi1`、`gearbox_temp_cma_t2` | 档位、°C、°C |

实际可读取的通道取决于车辆和当前配置。制作跨车型主题时优先使用常用通道，并为厂家通道提供可替换的数据槽。写进主题的 `parameter` 应来自 EasyDash 参数列表或用户提供的车辆配置。标准 MAP 是绝对压力，若要显示相对增压值，还需要相应的基准压力或已换算的车辆通道。

## 带图片或音效时再读

**图片。** 静态背景可用 `{"type":"image","x":0,"y":0,"width":960,"height":540,"url":"resource:pitwall.webp","fit":"cover"}`。分享时把 `pitwall.webp` 一起打包。支持 PNG、JPEG、WebP，最多 64 张，单张最多 8 MiB、每边最多 8192、总像素最多 16,777,216。文件名使用英文字母、数字、点、下划线或连字符，首字符为字母或数字。同包文件名忽略大小写也应唯一。`resource:` 后仅写文件名。

**转速切图。** `rpmImage` 可绑定 `parameter: "rpm"`，用 `idleUrl`、`focusUrl`、`redlineUrl` 引用三张包内图，并设置 `idleThreshold` 和 `redlineThreshold`。例如 2200 和 4500 RPM 对应低于 2200、2200 至 4499、4500 及以上三态。让各状态图尺寸、构图和人物锚点一致，即可在切换时保持镜头稳定。

**阈值音效。** 在 manifest 根节点添加 `soundCues`。下例绑定转速槽，要求资源目录中有真实的 `shift.wav`。

```json
[
  {"id":"shift_cue","slot":"engine_speed","parameter":"rpm",
   "source":"resource:shift.wav","threshold":5000,"hysteresis":300,
   "minIntervalMs":3000,"volume":0.45}
]
```

首次从低于 5000 到达阈值时响一次。回落到 4700 或更低后才能再次触发，两次播放至少间隔 3 秒。首次读数已经很高时，需先看到低于阈值的读数。每条提示使用唯一 `id`，`hysteresis` 大于 0，`minIntervalMs` 为 250 至 60000 的整数，`volume` 为 0 至 1。最多 8 条提示及 8 份音频。每段最长 3 秒、最多 600 KiB，使用 8–48 kHz、16 位小端无压缩 PCM WAV，单声道或双声道。需要同期显示图像时，给一个 `image` 配置相同的 `cueId` 和 `focusUrl: "resource:flash.png"`，它会在这条声音播放时显示。

**交付文件。** 可分享的 `作品名.easydash.json` 是 UTF-8 JSON。外层使用 `format: "easydash.theme"` 和 `version: 1`，内层 `watchface` 放 manifest，`resources` 放图片的 Base64，`audioResources` 放音频的 Base64。全部素材原始字节合计最多 24 MiB，编码后的完整文件最多 32 MiB。无素材主题用空的 `resources`。编辑器打开和手机导入都使用这份文件。
