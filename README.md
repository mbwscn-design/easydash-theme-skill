# EasyDash 仪表主题生成 Skill

用中文描述想做的汽车仪表，得到可以在 EasyDash Studio 编辑、在手机 EasyDash 导入的 `.easydash.json`。可从零设计，也可基于原主题换肤，沿用用户已经绑定的原车通道。

![《黄线俱乐部》在模拟数据下的画面](skills/easydash-theme/assets/preview.png)

## 选你平时用的工具

| 工具 | 从哪里开始 | 怎样拿到主题 |
| --- | --- | --- |
| 豆包、DeepSeek 等聊天工具 | 复制[通用对话提示词](skills/easydash-theme/references/通用对话提示词.txt)，在「我的需求」后写上想做的仪表，整段发到新对话 | 复制回复中的完整 JSON，用下方离线工具保存 |
| WorkBuddy 桌面端 | 下载 [WorkBuddy 技能包](downloads/easydash-theme-workbuddy.zip?raw=true)，在「专家·技能·连接器 → 技能 → 添加技能 → 上传技能」选择此 ZIP | 在「已安装」启用技能，新任务选定工作文件夹和 EasyDash 技能，让它把主题保存到该文件夹 |
| Codex | 下载 [Codex 技能包](downloads/easydash-theme.zip?raw=true)，解压到项目的 `.agents/skills/`，确认有 `easydash-theme/SKILL.md` | 在该项目新建对话，输入 `$easydash-theme` 加上你的需求 |

可以从这句话开始：

> 做一套黑黄横屏仪表。左侧用大数字显示车速，右侧用分块环显示转速，下方放水温和保留一位小数的电压卡。每个数据位都能在手机上重新绑定。交付可编辑的 EasyDash 主题。

普通聊天模式可直接生成数值卡、条形表、指针和转速环。想在旧主题上更换图片、保留已有音效和槽位，可以把原文件与素材放入 WorkBuddy 或 Codex 的工作目录。打包脚本使用 Python 3 标准库。[豆包](https://www.doubao.com/chat/) · [DeepSeek](https://chat.deepseek.com/) · [WorkBuddy 官方技能指南](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)

## 把聊天回复导入 EasyDash

1. 在电脑浏览器打开[离线下载工具的文件页](skills/easydash-theme/references/chat-to-theme.html)，点 GitHub 文件工具栏里的「Download raw file」，然后双击下载的 `chat-to-theme.html`。也可直接打开解压包内的 `references/chat-to-theme.html`。
2. 粘贴完整 JSON 或整个 JSON 代码块，点击「下载主题文件」。页面在本机检查格式并保存文件。只用手机时，也可以用纯文本编辑器以 UTF-8 保存为 `作品名.easydash.json`。
3. 在电脑 EasyDash Studio 里点「打开工程」，选文件后播放模拟数据。手机上打开 EasyDash「主题中心 → 导入主题」，选择同一文件。

## 示例和进阶用法

- [下载可直接导入的示例主题《黄线俱乐部》](examples/yellowline-club.easydash.json?raw=true)
- [七组中文提示词与使用说明](skills/easydash-theme/使用与提示词.md) · [下载纯文本场景示例](downloads/用户生成提示词.txt?raw=true)
- [主题格式、通道 ID 和音效](skills/easydash-theme/references/theme-format.md) · [技能源码](skills/easydash-theme/SKILL.md) · [下载 .skill 格式](downloads/easydash-theme.skill?raw=true)

## 开源许可

本仓库采用 [MIT 许可证](LICENSE)，版权署名为 mbwscn-design。再分发本软件或其实质部分时，请保留版权和许可声明。
