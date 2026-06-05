# mai_amamiya

Bangumi 在看动画每日简报推送项目。

这个仓库使用 GitHub Actions 定时读取 Bangumi 用户 `jasumin` 的当前在看动画，结合 Bangumi 官方 API 中的收藏进度和章节放送信息，生成中文简报后通过 Bark 推送到 iPhone。仓库同时保存 Bark 通知使用的自定义图标。

## 功能

- 每天自动生成 Bangumi 在看动画简报
- 使用 Bangumi 官方 API 读取当前在看收藏和 `ep_status`
- 使用 `v0/episodes` 接口读取章节、放送日期和下一话日期
- 将“已放送但未追上”的条目放在“优先看”
- 通过 Bark 推送到 iPhone
- 推送使用自定义图标 `icon.jpg`
- 支持在 GitHub Actions 页面手动运行

## 运行时间

GitHub Actions 使用 UTC 时间配置：

```yaml
cron: "0 4 * * *"
```

对应北京时间每天 `12:00`。

## 必填 Secrets

在仓库页面进入：

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

添加以下两个 Repository secrets：

```text
BANGUMI_TOKEN
```

填写 Bangumi API Token。

```text
BARK_DEVICE_KEY
```

填写 Bark 推送 URL 中 `https://api.day.app/` 后面的 device key。

不要把 Token 或 Bark key 写进代码、README、Issue 或 Actions 日志。

## 手动运行

进入仓库的 `Actions` 页面：

1. 选择 `Bangumi brief`
2. 点击 `Run workflow`
3. 选择 `main`
4. 再次点击 `Run workflow`

运行成功后，Bark 会收到一条标题类似下面的推送：

```text
Bangumi 在看简报｜YYYY-MM-DD
```

## 文件结构

```text
.github/workflows/bangumi-brief.yml  # GitHub Actions 定时任务
scripts/bangumi_brief.py             # Bangumi 读取与 Bark 推送脚本
icon.jpg                             # Bark 自定义推送图标
```

## 图标

当前 Bark 图标直链：

```text
https://raw.githubusercontent.com/Jasumin/mai_amamiya/main/icon.jpg
```

如需替换图标，直接替换仓库根目录下的 `icon.jpg`。建议使用正方形 JPG/PNG，文件尽量小于 `500 KB`。

## 本地测试

如果需要在本地测试，可以设置环境变量后运行：

```powershell
$env:BANGUMI_TOKEN="your_bangumi_token"
$env:BARK_DEVICE_KEY="your_bark_device_key"
python scripts\bangumi_brief.py
```

脚本不会打印密钥，但会把生成结果发送到 Bark。
