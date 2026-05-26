#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from LLM.zeiss_gateway_client import ZeissLLMGatewayClient, dump_json


DEFAULT_BASE_URL = "https://api.genai.zeiss.com/llm"


def _load_body(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    if getattr(args, "body_file", None):
        with open(args.body_file, "r", encoding="utf-8") as f:
            return json.load(f)

    if getattr(args, "body", None):
        return json.loads(args.body)

    return None


def _parse_kv_pairs(items: Optional[list]) -> Optional[Dict[str, Any]]:
    if not items:
        return None
    out: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid key-value '{item}'. Expected key=value")
        key, value = item.split("=", 1)
        out[key] = value
    return out


def _client_from_args(args: argparse.Namespace) -> ZeissLLMGatewayClient:
    api_key = args.api_key or os.getenv("ZEISS_SUB_KEY")
    if not api_key:
        raise ValueError("API key missing. Use --api-key or set ZEISS_SUB_KEY env var.")

    return ZeissLLMGatewayClient(
        base_url=args.base_url,
        api_key=api_key,
        timeout=args.timeout,
    )


def _write_output(data: Any, output_path: Optional[str]) -> None:
    text = dump_json(data)
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"Saved response to: {out_path}")
        return

    print(text)


def cmd_models_list(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    params = _parse_kv_pairs(args.param)
    data = client.list_models(version=args.version, params=params)
    _write_output(data, args.output)


def cmd_models_get(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.get_model(args.model_id, version=args.version)
    _write_output(data, args.output)


def cmd_model_info(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.model_info(version=args.version, litellm_model_id=args.litellm_model_id)
    _write_output(data, args.output)


def cmd_chat(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        if not args.model:
            raise ValueError("Provide --model when body is not supplied.")
        messages = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        if args.user:
            messages.append({"role": "user", "content": args.user})
        if not messages:
            raise ValueError("Provide at least --user or --body/--body-file.")

        body = {
            "model": args.model,
            "messages": messages,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
        }

    data = client.chat_completions(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_completions(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        raise ValueError("Completions requires --body or --body-file")
    data = client.completions(deployment=args.deployment, body=body)
    _write_output(data, args.output)


def cmd_embeddings(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        if not args.model or not args.input:
            raise ValueError("Provide --model and --input, or use --body/--body-file")
        body = {"model": args.model, "input": [args.input]}

    data = client.embeddings(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_audio_speech(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        raise ValueError("Audio speech requires --body or --body-file")
    data = client.audio_speech(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_audio_transcriptions(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        raise ValueError("Audio transcriptions requires --body or --body-file")
    data = client.audio_transcriptions(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_assistants_list(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.list_assistants(version=args.version)
    _write_output(data, args.output)


def cmd_assistants_create(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        raise ValueError("Create assistant requires --body or --body-file")
    data = client.create_assistant(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_assistants_delete(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.delete_assistant(args.assistant_id, version=args.version)
    _write_output(data, args.output)


def cmd_responses_create(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    body = _load_body(args)
    if body is None:
        if not args.model or not args.input:
            raise ValueError("Provide --model and --input, or use --body/--body-file")
        body = {
            "model": args.model,
            "input": args.input,
            "max_output_tokens": args.max_output_tokens,
        }
        if args.background:
            body["background"] = True

    data = client.create_response(body=body, version=args.version)
    _write_output(data, args.output)


def cmd_responses_get(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.get_response(args.response_id, version=args.version)
    _write_output(data, args.output)


def cmd_responses_delete(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.delete_response(args.response_id, version=args.version)
    _write_output(data, args.output)


def cmd_responses_cancel(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.cancel_response(args.response_id, version=args.version)
    _write_output(data, args.output)


def cmd_responses_input_items(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.response_input_items(args.response_id, version=args.version)
    _write_output(data, args.output)


def cmd_key_info(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    data = client.key_info(key=args.key)
    _write_output(data, args.output)


def cmd_spend_logs(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    params = _parse_kv_pairs(args.param)
    data = client.spend_logs(params=params)
    _write_output(data, args.output)


def cmd_user_activity(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    params = _parse_kv_pairs(args.param)
    data = client.user_daily_activity(params=params)
    _write_output(data, args.output)


def cmd_raw(args: argparse.Namespace) -> None:
    client = _client_from_args(args)
    params = _parse_kv_pairs(args.param)
    body = _load_body(args)
    data = client.request(args.method, args.path, params=params, body=body)
    _write_output(data, args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZEISS LLM Gateway CLI")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Gateway base URL")
    parser.add_argument("--api-key", default=None, help="ZEISS subscription key. Defaults to ZEISS_SUB_KEY env var.")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--output", default=None, help="Output file to save JSON response")

    # Models
    p = subparsers.add_parser("models-list", help="GET /models or /v1/models")
    p.add_argument("--version", choices=["plain", "v1"], default="plain")
    p.add_argument("--param", action="append", help="Query parameter key=value (repeatable)")
    add_common_flags(p)
    p.set_defaults(func=cmd_models_list)

    p = subparsers.add_parser("models-get", help="GET /models/{id} or /v1/models/{id}")
    p.add_argument("model_id")
    p.add_argument("--version", choices=["plain", "v1"], default="plain")
    add_common_flags(p)
    p.set_defaults(func=cmd_models_get)

    p = subparsers.add_parser("model-info", help="GET /model/info or /v1/model/info")
    p.add_argument("--version", choices=["plain", "v1"], default="plain")
    p.add_argument("--litellm-model-id", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_model_info)

    # Chat
    p = subparsers.add_parser("chat", help="POST /chat/completions or /v1/chat/completions")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    p.add_argument("--model", default=None)
    p.add_argument("--system", default=None)
    p.add_argument("--user", default=None)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--body", default=None, help="Raw JSON string")
    p.add_argument("--body-file", default=None, help="Path to JSON body file")
    add_common_flags(p)
    p.set_defaults(func=cmd_chat)

    # Legacy completions deployment route
    p = subparsers.add_parser("completions", help="POST /openai/deployments/{deployment}/completions")
    p.add_argument("deployment")
    p.add_argument("--body", default=None, help="Raw JSON string")
    p.add_argument("--body-file", default=None, help="Path to JSON body file")
    add_common_flags(p)
    p.set_defaults(func=cmd_completions)

    # Embeddings
    p = subparsers.add_parser("embeddings", help="POST /embeddings or /v1/embeddings")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    p.add_argument("--model", default=None)
    p.add_argument("--input", default=None, help="Single input text")
    p.add_argument("--body", default=None)
    p.add_argument("--body-file", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_embeddings)

    # Audio
    p = subparsers.add_parser("audio-speech", help="POST /audio/speech or /v1/audio/speech")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    p.add_argument("--body", default=None)
    p.add_argument("--body-file", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_audio_speech)

    p = subparsers.add_parser("audio-transcriptions", help="POST /audio/transcriptions or /v1/audio/transcriptions")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    p.add_argument("--body", default=None)
    p.add_argument("--body-file", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_audio_transcriptions)

    # Assistants
    p = subparsers.add_parser("assistants-list", help="GET /assistants or /v1/assistants")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_assistants_list)

    p = subparsers.add_parser("assistants-create", help="POST /assistants or /v1/assistants")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    p.add_argument("--body", default=None)
    p.add_argument("--body-file", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_assistants_create)

    p = subparsers.add_parser("assistants-delete", help="DELETE /assistants/{id} or /v1/assistants/{id}")
    p.add_argument("assistant_id")
    p.add_argument("--version", choices=["plain", "v1"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_assistants_delete)

    # Responses
    p = subparsers.add_parser("responses-create", help="POST /responses, /v1/responses or /openai/v1/responses")
    p.add_argument("--version", choices=["plain", "v1", "openai"], default="v1")
    p.add_argument("--model", default=None)
    p.add_argument("--input", default=None)
    p.add_argument("--max-output-tokens", type=int, default=1024)
    p.add_argument("--background", action="store_true")
    p.add_argument("--body", default=None)
    p.add_argument("--body-file", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_responses_create)

    p = subparsers.add_parser("responses-get", help="GET response by id")
    p.add_argument("response_id")
    p.add_argument("--version", choices=["plain", "v1", "openai"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_responses_get)

    p = subparsers.add_parser("responses-delete", help="DELETE response by id")
    p.add_argument("response_id")
    p.add_argument("--version", choices=["plain", "v1", "openai"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_responses_delete)

    p = subparsers.add_parser("responses-cancel", help="POST response cancel")
    p.add_argument("response_id")
    p.add_argument("--version", choices=["plain", "v1", "openai"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_responses_cancel)

    p = subparsers.add_parser("responses-input-items", help="GET response input items")
    p.add_argument("response_id")
    p.add_argument("--version", choices=["plain", "v1", "openai"], default="v1")
    add_common_flags(p)
    p.set_defaults(func=cmd_responses_input_items)

    # Key + Spend
    p = subparsers.add_parser("key-info", help="GET /key/info")
    p.add_argument("--key", default=None)
    add_common_flags(p)
    p.set_defaults(func=cmd_key_info)

    p = subparsers.add_parser("spend-logs", help="GET /spend/logs")
    p.add_argument("--param", action="append", help="Query parameter key=value (repeatable)")
    add_common_flags(p)
    p.set_defaults(func=cmd_spend_logs)

    p = subparsers.add_parser("user-activity", help="GET /user/daily/activity")
    p.add_argument("--param", action="append", help="Query parameter key=value (repeatable)")
    add_common_flags(p)
    p.set_defaults(func=cmd_user_activity)

    # Raw fallback for any endpoint in collection
    p = subparsers.add_parser("raw", help="Call any endpoint path directly")
    p.add_argument("--method", required=True, help="HTTP method")
    p.add_argument("--path", required=True, help="Endpoint path (e.g., /v1/models)")
    p.add_argument("--param", action="append", help="Query parameter key=value (repeatable)")
    p.add_argument("--body", default=None, help="Raw JSON string")
    p.add_argument("--body-file", default=None, help="Path to JSON body file")
    add_common_flags(p)
    p.set_defaults(func=cmd_raw)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
