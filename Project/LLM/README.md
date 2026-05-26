# ZEISS LLM Gateway Scripts

This folder provides a Python client and CLI to call ZEISS LLM Gateway endpoints from the Postman collection.

## Files

- LLM/zeiss_gateway_client.py: Reusable API client.
- scripts/llm_gateway_cli.py: Command-line wrapper with endpoint-specific subcommands.

## Setup

Use your existing project environment and set API key:

```powershell
$env:ZEISS_SUB_KEY="<your-zeiss-subscription-key>"
```

## Tkinter Desktop UI

Launch the integrated desktop app:

```powershell
python scripts/framework_ui.py
```

The UI supports:
- URL scraping + selector prediction (`predict` workflow)
- Full end-to-end helper generation (`generate-js` workflow)
- All LLM parameters from terminal flow (model, version, temperature, max tokens, base URL, prompt file, subscription key)
- Live processing log stream
- One-click open for generated helper JS file

Optional base URL override (default is `https://api.genai.zeiss.com/llm`):

```powershell
python scripts/llm_gateway_cli.py --base-url https://api.genai.zeiss.com/llm models-list
```

## Common Commands

### Model management

```powershell
python scripts/llm_gateway_cli.py models-list --version v1
python scripts/llm_gateway_cli.py models-get gpt-4o --version v1
python scripts/llm_gateway_cli.py model-info --version v1
```

### Chat completions

```powershell
python scripts/llm_gateway_cli.py chat --version v1 --model gpt-4o --system "You are helpful" --user "Hello"
```

### Embeddings

```powershell
python scripts/llm_gateway_cli.py embeddings --version v1 --model text-embedding-3-small --input "hello world"
```

### Responses API

```powershell
python scripts/llm_gateway_cli.py responses-create --version v1 --model gpt-4o --input "Summarize test automation"
python scripts/llm_gateway_cli.py responses-get <response_id> --version v1
python scripts/llm_gateway_cli.py responses-cancel <response_id> --version v1
python scripts/llm_gateway_cli.py responses-delete <response_id> --version v1
```

### Assistants

```powershell
python scripts/llm_gateway_cli.py assistants-list --version v1
python scripts/llm_gateway_cli.py assistants-create --version v1 --body-file .\LLM\payloads\assistant_create.json
```

### Audio

```powershell
python scripts/llm_gateway_cli.py audio-speech --version v1 --body-file .\LLM\payloads\audio_speech.json
python scripts/llm_gateway_cli.py audio-transcriptions --version v1 --body-file .\LLM\payloads\audio_transcription.json
```

### Key / spend

```powershell
python scripts/llm_gateway_cli.py key-info
python scripts/llm_gateway_cli.py spend-logs --param start_date=2026-01-01 --param end_date=2026-01-31
python scripts/llm_gateway_cli.py user-activity --param start_date=2026-01-01 --param end_date=2026-01-31
```

### Raw endpoint (fallback)

For any endpoint variant not covered by subcommands:

```powershell
python scripts/llm_gateway_cli.py raw --method GET --path /v1/models
python scripts/llm_gateway_cli.py raw --method POST --path /v1/chat/completions --body-file .\LLM\payloads\chat.json
```

## Save responses to file

Add `--output`:

```powershell
python scripts/llm_gateway_cli.py models-list --version v1 --output .\LLM\out\models.json
```
