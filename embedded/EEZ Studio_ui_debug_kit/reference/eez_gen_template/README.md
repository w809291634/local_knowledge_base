# 通用 EEZ 生成器模板（LVGL / no flow）

目标：工程侧只写 `design_source.json`，生成器负责克隆模板、字体、跳转与硬门禁；
避免每个工程各写一套 `build_ui.py`，再次出现按钮子标签等大、Slider 轨道变粗等问题。

## 用法

```bash
python tools/eez_gen_template.py \
  --src   <工程>/design/design_source.json \
  --base  <工程>/design/eez_base.json \
  --out   <工程>/xxx.eez-project \
  --base-dir <工程>
```

复检：

```bash
python tools/template_field_check.py <工程>/xxx.eez-project   # A14 字段集
python tools/check_button_child.py <工程>/xxx.eez-project     # BTN_CHILD
```

## design_source.json 契约

```json
{
  "screen": {"w": 800, "h": 480},
  "theme": {"bg": "#060B13"},
  "ttf_by_token": {"cn16": "fonts/msyh.ttf",
                   "cn24": "fonts/msyhbd.ttf", "cn64": "fonts/msyhbd.ttf"},
  "pages": [
    {
      "name": "主监护", "key": "main", "h5_only": false,
      "width": 800, "height": 480,
      "screen": {"children": [
        {"type": "container", "x": 16, "y": 88, "w": 520, "h": 160,
         "fill": "#0F1724", "fill_opa": 255, "stroke": "#223146", "radius": 10},
        {"type": "label", "x": 568, "y": 117, "w": 75, "h": 54,
         "text": "78", "font": "cn64", "color": "#EDF4FF",
         "align": "left", "text_opa": 255, "role": "read"},
        {"type": "button", "x": 16, "y": 6, "w": 250, "h": 24,
         "text": "患者信息", "font": "cn16", "color": "#EDF4FF",
         "align": "center", "fill": "#162233", "stroke": "#223146",
         "radius": 6, "transparent": false, "text_hidden": false,
         "goto": "患者信息"},
        {"type": "switch", "x": 700, "y": 276, "w": 44, "h": 24},
        {"type": "slider", "x": 220, "y": 96, "w": 300, "h": 24,
         "track_y": 100, "value": 65, "color": "#FF6B7A"},
        {"type": "line", "x": 28, "y": 133, "w": 496, "h": 83,
         "points": "0,38 20,38 30,0 ...", "color": "#3FD0C9", "width": 2}
      ]}
    }
  ]
}
```

## 内置硬规则

- 控件只从 `reference/eez_widget_syntax/templates/` 克隆；字段集不超模板（A14）。
- 按钮子标签永远 `content`；禁止等于按钮盒；内置 `BTN_CHILD` 断言。
- 居中按钮 `align/text_align=CENTER`；左/右例外 `LEFT_MID/RIGHT_MID` + 父 pad。
- Slider `MAIN` 透明；6px 轨道由设计源的独立容器提供；`top=track_y-9`（有 `ezz_y` 时以 `ezz_y` 为准）；`KNOB pad=-4`。
- 读数 Label 用设计原文实测盒，不用 H5 点击热区盒。
- 字体按 token 分 TTF；无 `text-anchor` 按 middle。
- `connectionLines` 固定为空；跳转只落控件 `eventHandlers`（no flow）。

## 说明

- `eez_base.json` 是工程骨架（LVGL 9.4、800×480、darkTheme、src/ui 输出）。
- 页面名用 `key`（ASCII），中文只放 `name` 供人看。
- 生成后仍需走 EEZ 构建、字体烘焙、C 语法、A/B1 与真机流程，不以生成成功替代验收。
