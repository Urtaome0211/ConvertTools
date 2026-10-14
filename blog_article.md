# 手写一个扁平化格式转换工具箱：ConvertTools 开发手记

> 用 Python + PySide6 从零打造一个本地桌面格式转换工具，从初版的六大场景扩展到十三项功能（v1.1 新增：PDF 压缩 / 拆分 / 加密水印、图片与音频格式互转、视频压缩、视频转 GIF）。本文复盘整个项目的技术选型、架构设计与踩坑记录。

---

## 一、缘起：为什么又是「格式转换」？

格式转换是一个被做烂了的需求，也是一个永远做不完的需求。网上在线转换站多如牛毛，但把文件丢给陌生服务器，隐私和文件大小都是问题；桌面端虽然有各种大而全的「办公套件」，但往往臃肿、弹广告、装一堆全家桶。

于是我给自己定了一个小目标：写一个**扁平化、无广告、纯本地**的格式转换工具箱，只做最常用的几个场景，界面清爽，拖进去就能转。这就是 ConvertTools。

## 二、技术选型：为什么是 PySide6？

桌面 GUI 的候选很多，逐个排除：

| 方案 | 排除原因 |
| --- | --- |
| Tkinter | 样式老旧，做「扁平化」要花大量力气还不好看 |
| Electron | 打包体积 100MB+，内存占用高，杀鸡用牛刀 |
| wxPython | 控件观感偏 Win32 老派，QSS 式主题能力弱 |
| **PySide6 (Qt 6)** | ✅ 官方 Qt for Python 绑定，LGPL 宽松协议，QSS 一套样式表即可实现扁平化 |

Qt 的 QSS 和 CSS 高度相似，写一个「浅底 + 白卡片 + 圆角 + 无渐变」的扁平化主题也就是几十行的样式表，主按钮一个主题色搞定：

```css
QPushButton#primary {
    background: #4A7CF7; color: white;
    border: none; border-radius: 6px; padding: 8px 22px;
}
QFrame#card {
    background: white; border-radius: 10px;
    border: 1px solid #E8EAF0;
}
```

转换引擎方面，全部选择成熟库而不是自己造轮子：

- **PDF ⇄ Word**：pdf2docx（PDF→Word 版面解析很成熟）；Word→PDF 则交给本机 Microsoft Office 的 COM 自动化——`SaveAs(..., FileFormat=17)` 一行就出完美排版。
- **PDF ⇄ 图片**：PyMuPDF 逐页渲染，可调 DPI；图片→PDF 用 Pillow 合成。
- **Excel ⇄ PDF**：Excel→PDF 同样走 COM（`ExportAsFixedFormat`）；PDF→Excel 用 pdfplumber 抽表格，每页一个工作表。
- **视频 / 音视频**：ffmpeg，H.264+AAC 出 mp4/mkv/flv，MPEG-4+MP3 出 avi（兼容性优先）。

## 三、架构：逻辑与界面彻底分层

源码按「每页一个文件」组织，核心约定是 **core 层不 import 任何 Qt 模块**：

```
app/
├── core/      # 纯逻辑：每个转换函数签名统一，可脱离 GUI 单独测试
├── ui/        # 界面：pages/ 下每页一个文件，继承统一的基类
├── workers.py # 后台线程封装
└── style.py   # 全局 QSS
```

两个值得记录的设计决策：

### 1. 统一的任务签名

所有转换函数遵循同一个回调式签名，进度、日志、取消全部通过回调外抛：

```python
def convert_video(src, out, fmt, crf=23, on_progress=None, on_log=None, is_cancelled=None): ...
```

`on_progress` 收 0–100 的整数，或 `None` 表示「忙碌中」；GUI 收到 `None` 就把进度条切成无限滚动模式。这样 core 层完全不知道界面的存在，单元测试里传个 `print` 就能跑。

### 2. 后台线程 + 信号

界面卡死是转换类工具的头号大忌。用 `QThread` 子类封装后台任务，进度/日志/完成都走 Qt 信号队列，线程安全天然保证：

```python
class TaskWorker(QThread):
    progress = Signal(object)      # int 0-100 或 None
    log = Signal(str)
    finished = Signal(bool, str)   # (是否全部成功, 摘要)
```

任务函数里调用 `is_cancelled()` 检查取消标志并抛 `CancelledError`，外层捕获后静默收场——用户点「取消」不会看到报错弹窗，这是细节体验。

## 四、几个真正费功夫的坑

### 坑 1：ffmpeg 的进度，比你想象的难拿

ffmpeg 的进度信息默认打在 stderr 上，而且和日志混在一起。常规做法是加 `-progress pipe:1 -nostats`，让它把进度以 key=value 形式输出到 stdout：

```
out_time_us=1500000
progress=continue
```

但有两个隐藏坑：

- **管道阻塞**：ffmpeg 的 stderr 是主动输出的，如果不开管道去读，缓冲区满了转换会直接卡死。所以必须 `-loglevel error`（把错误也压进管道）或者把 stderr 接到管道上。
- **单位陷阱**：`out_time_ms` 这个键名里的单位其实也是**微秒**（老版本的历史遗留 bug 沿用至今），直接用毫秒去算会得到 1000 倍的进度，进度条当场爆表。所以要么只用 `out_time_us`，要么两个键都按微秒处理。

另外 Windows 上要用 `CREATE_NO_WINDOW` 标志，否则每启动一次 ffmpeg 都会闪一个黑框。

### 坑 2：COM 自动化不是随便调的

pywin32 调 Word/Excel 有三个注意点：

- 用 `DispatchEx` 而不是 `Dispatch`，保证每次都是独立的 Office 实例，互不干扰；
- 调用发生在后台线程时，必须自己 `CoInitialize()`，否则 COM 直接报错；
- `Quit()` 要放在 `finally` 里，转换失败也不能留下僵尸进程——不然任务管理器里会攒出一排 WINWORD.EXE。

### 坑 3：PDF→Excel 的边界要诚实

pdfplumber 只能提取「结构化的表格」，扫描件、图片型 PDF 上根本没有文本层，什么库都救不了。与其硬凑功能，不如在界面副标题里就写明「扫描件无法提取」，日志里再给一次提示。工具的边界讲清楚，比转出一个四不像更让用户信任。

### 坑 4：提取视频轨不能想当然

「从视频里去掉声音」直觉做法是 `-c:v copy -an` 流复制，快且无损。但 copy 出来的视频流放进某些容器会不兼容（比如 mp4 视频流塞进 avi）。稳妥策略：先尝试 copy，失败自动回退到 libx264 重编码，用户无感知，成功率拉满。

## 五、v1.1 升级：七项新功能是怎么长出来的

初版交付后，v1.1 一口气加了七个功能页：PDF 压缩（无损 / 有损）、PDF 拆分（每页 / 每 N 页 / 自定义范围）、PDF 加密解密与水印、图片格式互转（五种格式 + 缩放 + 质量）、音频格式互转（六种格式）、视频压缩与改分辨率、视频转 GIF。加上两个体验改进——记住上次参数、完成提示音 + 弹窗——导航页从 7 个涨到 14 个。

得益于初版「每页一个文件 + core 层无 Qt 依赖」的架构，加功能几乎是机械劳动：core 层写一个符合统一回调签名的函数，pages 下复制一个页面骨架，`NAV_ITEMS` 里注册一行。七个功能页共享的样板代码远多于各自的逻辑。

但机械劳动里也有三个新坑：

**坑 5：PyMuPDF 的文字旋转只有四个角度。** `page.insert_text(..., rotate=45)` 直接抛 `ValueError: bad rotate value`——rotate 参数只接受 90° 的倍数，水印要 45° 斜排怎么办？答案是干脆不用矢量文字：先用 Pillow 把水印文字画到透明 PNG 上，`Image.rotate()` 任意角度旋转后再以图片形式插入 PDF。代价是文字变成栅格，但水印本来就是视觉元素，无伤大雅；反而文字和图片两种水印从此共用同一条插入路径，代码更短了。

**坑 6：极短视频的「压缩」会变大。** 冒烟测试里用 2 秒、30KB 的样例视频测视频压缩，断言「输出 < 输入」，结果 x264 的编码与封装开销让输出反而更大——测试红了，代码没毛病。修正思路是把断言改成行为对比：同一段视频分别用 CRF 33 与 CRF 20 压缩，验证「低画质档位体积更小」。在极值样本下测行为而不是测绝对值，这条经验对任何压缩类功能都成立。

**坑 7：参数记忆的「注册表」模式。** 记住上次参数最怕每个页面各写一套读写逻辑。基类里做一个 `_register_setting(widget, name)`：传入控件和名字，内部按控件类型（QComboBox / QSpinBox / QCheckBox / QLineEdit…）分派读写 QSettings，启动时恢复、变更即保存。每个页面只需在构造函数里追加几行注册，零重复代码。

## 六、交付与反思

项目最终交付三样东西：可运行的程序、README、以及这篇手记。另外我还留了一个 `tests/smoke_test.py` 的端到端冒烟测试：脚本自动生成样例 PDF/Word/Excel/图片/视频，然后把**全部**转换功能（包括 COM 和 ffmpeg）真实跑一遍，GUI 也离屏启动验证——一条命令回归全部功能。

复盘下来，三点体会最深：

1. **接口先行**：core 层统一回调签名之后，UI、测试、命令行三处复用同一份逻辑，后期的维护成本低得惊人。
2. **依赖声明要诚实**：Word/Excel→PDF 依赖本机 Office，就把这条写进 README 和界面提示，而不是静默失败。
3. **细节决定质感**：取消不弹报错、进度条忙碌态、单文件失败不中断批量任务——这些「小」体验加起来，才是一个工具而不是玩具。

源码已开源在项目目录（v1.1.0），欢迎取用和提改进建议。如果这篇手记对你有用，就点个赞吧。
