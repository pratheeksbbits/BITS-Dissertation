import json
from typing import Any, Dict, Optional

import requests


class ZeissLLMGatewayClient:
    """Minimal client for ZEISS LLM Gateway endpoints.

    Auth header follows the provided collection: api-key: <subscription-key>
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 120):
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "api-key": api_key,
                "Content-Type": "application/json",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        raw_body: Optional[str] = None,
    ) -> Any:
        if not path.startswith("/"):
            path = f"/{path}"

        url = f"{self.base_url}{path}"

        kwargs: Dict[str, Any] = {
            "params": params,
            "timeout": self.timeout,
        }

        if raw_body is not None:
            kwargs["data"] = raw_body
        elif body is not None:
            kwargs["json"] = body

        response = self.session.request(method=method.upper(), url=url, **kwargs)

        # Raise rich error text early for easier debugging.
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            details = response.text[:2000]
            raise requests.HTTPError(f"{exc}\nResponse: {details}") from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()

        return {
            "status_code": response.status_code,
            "content_type": content_type,
            "text": response.text,
        }

    # Model Management
    def list_models(self, version: str = "plain", params: Optional[Dict[str, Any]] = None) -> Any:
        path = "/models" if version == "plain" else "/v1/models"
        return self.request("GET", path, params=params)

    def get_model(self, model_id: str, version: str = "plain") -> Any:
        path = f"/models/{model_id}" if version == "plain" else f"/v1/models/{model_id}"
        return self.request("GET", path)

    def model_info(self, version: str = "plain", litellm_model_id: Optional[str] = None) -> Any:
        path = "/model/info" if version == "plain" else "/v1/model/info"
        params = {"litellm_model_id": litellm_model_id} if litellm_model_id else None
        return self.request("GET", path, params=params)

    # Chat / Completions / Embeddings
    def chat_completions(self, body: Dict[str, Any], version: str = "plain") -> Any:
        path = "/chat/completions" if version == "plain" else "/v1/chat/completions"
        return self.request("POST", path, body=body)

    def completions(self, deployment: str, body: Dict[str, Any]) -> Any:
        path = f"/openai/deployments/{deployment}/completions"
        return self.request("POST", path, body=body)

    def embeddings(self, body: Dict[str, Any], version: str = "plain") -> Any:
        path = "/embeddings" if version == "plain" else "/v1/embeddings"
        return self.request("POST", path, body=body)

    # Audio
    def audio_speech(self, body: Dict[str, Any], version: str = "plain") -> Any:
        path = "/audio/speech" if version == "plain" else "/v1/audio/speech"
        return self.request("POST", path, body=body)

    def audio_transcriptions(self, body: Dict[str, Any], version: str = "plain") -> Any:
        path = "/audio/transcriptions" if version == "plain" else "/v1/audio/transcriptions"
        return self.request("POST", path, body=body)

    # Assistants
    def list_assistants(self, version: str = "plain") -> Any:
        path = "/assistants" if version == "plain" else "/v1/assistants"
        return self.request("GET", path)

    def create_assistant(self, body: Dict[str, Any], version: str = "plain") -> Any:
        path = "/assistants" if version == "plain" else "/v1/assistants"
        return self.request("POST", path, body=body)

    def delete_assistant(self, assistant_id: str, version: str = "plain") -> Any:
        path = f"/assistants/{assistant_id}" if version == "plain" else f"/v1/assistants/{assistant_id}"
        return self.request("DELETE", path)

    # Responses API
    def create_response(self, body: Dict[str, Any], version: str = "plain") -> Any:
        if version == "openai":
            path = "/openai/v1/responses"
        elif version == "v1":
            path = "/v1/responses"
        else:
            path = "/responses"
        return self.request("POST", path, body=body)

    def get_response(self, response_id: str, version: str = "plain") -> Any:
        if version == "openai":
            path = f"/openai/v1/responses/{response_id}"
        elif version == "v1":
            path = f"/v1/responses/{response_id}"
        else:
            path = f"/responses/{response_id}"
        return self.request("GET", path)

    def delete_response(self, response_id: str, version: str = "plain") -> Any:
        if version == "openai":
            path = f"/openai/v1/responses/{response_id}"
        elif version == "v1":
            path = f"/v1/responses/{response_id}"
        else:
            path = f"/responses/{response_id}"
        return self.request("DELETE", path)

    def cancel_response(self, response_id: str, version: str = "plain") -> Any:
        if version == "openai":
            path = f"/openai/v1/responses/{response_id}/cancel"
        elif version == "v1":
            path = f"/v1/responses/{response_id}/cancel"
        else:
            path = f"/responses/{response_id}/cancel"
        return self.request("POST", path)

    def response_input_items(self, response_id: str, version: str = "plain") -> Any:
        if version == "openai":
            path = f"/openai/v1/responses/{response_id}/input_items"
        elif version == "v1":
            path = f"/v1/responses/{response_id}/input_items"
        else:
            path = f"/responses/{response_id}/input_items"
        return self.request("GET", path)

    # Key / Spend
    def key_info(self, key: Optional[str] = None) -> Any:
        params = {"key": key} if key else None
        return self.request("GET", "/key/info", params=params)

    def spend_logs(self, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", "/spend/logs", params=params)

    def user_daily_activity(self, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", "/user/daily/activity", params=params)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
