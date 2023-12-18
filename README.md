# Claude in Slack API for OpenAI and Anthropic API

本项目旨在将 Slack 中的 Claude 机器人封装为适用于 OpenAI 和 Anthropic 的 API 格式。从[claude-in-slack-api](https://github.com/yokonsan/claude-in-slack-api)改进而来。

## 纪念凉掉的 Slack 中的 Claude

虽然 Slack 的 Claude 已不再提供给普通用户，但如果你拥有企业 Slack 账号，尝试使用它仍然是值得的。通过结合 [one-api](https://github.com/songquanpeng/one-api) 项目，可以实现 API 分发。可同时支持 OpenAI 和 Anthropic 的 API 格式。

### 调用接口文档

接口文档地址：[http://127.0.0.1:8089/docs](http://127.0.0.1:8089/docs)

### 设置环境

请在 `.env` 文件中填入 Slack APP Token 和 Claude Bot ID。

### 安装与运行

确保你的系统已安装 Python 3.10 或以上版本。

安装依赖：
```bash
pip install -r requirements.txt
pip install sse-starlette
```

运行服务：
```bash
python claude2.0.py
```

服务将在 [http://127.0.0.1:8089](http://127.0.0.1:8089) 上运行。结合 one-api 可以实现 API 分发。可同时支持 OpenAI 和 Anthropic 的 API 格式。

### 获取 Slack APP Token 和 Claude Bot ID

关于如何获取 Slack APP Token 和 Claude Bot ID 的详细信息，请参考 [这篇教程](https://juejin.cn/post/7238917620849672247)。
