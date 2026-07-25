# Gemini MCP Server

A Docker-based MCP server that lets Claude (or any MCP client) call Google
Gemini models as tools. Follows the same pattern as the dice-roller example.

## Tools

- `gemini_ask(prompt, model?, temperature?)` — one-shot prompt.
- `gemini_chat(messages_json, model?, system?)` — multi-turn chat.
  `messages_json` is a JSON array like
  `[{"role":"user","text":"hi"},{"role":"model","text":"hello"}]`.
- `gemini_list_models()` — list models available to your API key.

Default model is `gemini-2.5-flash`; override with the `model` argument or
the `GEMINI_DEFAULT_MODEL` env var.

## Setup

### 1. Get a Gemini API key

Create one at <https://aistudio.google.com/apikey>.

### 2. Build the image

```bash
cd examples/gemini
docker build -t gemini-mcp-server .
```

### 3. Store the API key as a Docker MCP secret

```bash
docker mcp secret set GEMINI_API_KEY=YOUR_KEY_HERE
```

### 4. Register it with the Docker MCP catalog

Add this entry under `registry:` in `~/.docker/mcp/catalogs/custom.yaml`
(create the file if it doesn't exist — see `install_instructions.txt` for
the full template):

```yaml
gemini:
  description: "Call Google Gemini models from Claude"
  title: "Gemini"
  type: server
  image: gemini-mcp-server:latest
  tools:
    - name: gemini_ask
    - name: gemini_chat
    - name: gemini_list_models
  secrets:
    - name: GEMINI_API_KEY
      env: GEMINI_API_KEY
  metadata:
    category: ai
    tags: [gemini, google, llm]
    license: MIT
    owner: local
```

Then add `gemini: { ref: "" }` under `registry:` in
`~/.docker/mcp/registry.yaml` and restart Claude Desktop.

### 5. Run it manually (optional)

Useful for a quick check outside the gateway:

```bash
docker run --rm -i -e GEMINI_API_KEY=YOUR_KEY gemini-mcp-server
```

## Try it

Ask Claude:

- "Use gemini to summarize this article: …"
- "Get a second opinion from gemini-2.5-pro on my design."
- "List available Gemini models."
