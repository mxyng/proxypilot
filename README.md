# proxypilot

`proxypilot` is a simple addition to GitHub Copilot for local code completion. An existing Copilot subscription is required.

## Requirements

- Docker and Docker Compose
- [Ollama](https://github.com/jmorganca/ollama)

## Setup

```
ollama pull codellama:7b-code
docker compose up
```

## Configuring Copilot

### Neovim

Requires `github/copilot.vim`

```
# .vimrc
let g:copilot_proxy = 'http://localhost:61107'
let g:copilot_proxy_strict_ssl = false
```

```
# init.lua
vim.g.copilot_proxy = 'http://localhost:61107'
vim.g.copilot_proxy_strict_ssl = false
```

### Visual Studio Code

### JetBrains
