# local-figma-mcp

本地只读 Figma MCP Server，通过 `stdio` 给 Codex / Claude / Cursor 暴露 Figma REST API 工具。

## 1. 安装

```bash
cd /Users/oncechen/IdeaProjects/python3/local-figma-mcp
npm install
```

## 2. 准备 Figma token

在 Figma 创建 Personal access token，然后把它放进客户端 MCP 配置的 `env` 里。

也可以本地临时测试：

```bash
export FIGMA_ACCESS_TOKEN="figd_xxx"
npm run start
```

注意：MCP stdio server 的 stdout 只能给协议使用。这个项目只把启动错误写到 stderr。

## 3. Codex / Claude / Cursor 配置

```json
{
  "mcpServers": {
    "local-figma": {
      "command": "npm",
      "args": ["run", "start"],
      "cwd": "/Users/oncechen/IdeaProjects/python3/local-figma-mcp",
      "env": {
        "FIGMA_ACCESS_TOKEN": "figd_xxx"
      }
    }
  }
}
```

如果返回内容太长，可以调大截断上限：

```json
{
  "env": {
    "FIGMA_ACCESS_TOKEN": "figd_xxx",
    "FIGMA_MCP_MAX_RESPONSE_CHARS": "120000"
  }
}
```

## 4. Inspector 测试

```bash
cd /Users/oncechen/IdeaProjects/python3/local-figma-mcp
npm run inspect
```

## 5. 已提供工具

- `get_figma_file`: 读取文件 JSON，可限制 `depth`
- `get_figma_nodes`: 读取指定节点，可限制 `depth`
- `get_figma_images`: 导出节点图片链接，支持 `png` / `jpg` / `svg` / `pdf`
- `get_figma_components`: 读取文件组件
- `get_figma_styles`: 读取文件样式

Figma URL 里常见的 `node-id=1-2` 可以直接传，server 会自动转成 `1:2`。

## 6. 安全边界

- 只读 Figma API，不写 Figma 文件
- 不提供任意 shell 执行
- token 不写入仓库文件
- 建议先用 `get_figma_nodes` 读取小范围节点，避免大文件响应过长
