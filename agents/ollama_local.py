"""Client strictement local, sans téléchargement implicite ni redirection."""
import json
import urllib.request

class ModelError(Exception):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class OllamaLocal:
    def request(self, path, payload=None, timeout=180):
        if path not in ("/api/tags", "/api/chat", "/api/version"):
            raise ModelError("Route non autorisée")
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request("http://127.0.0.1:11434" + path, data=data,
                                         headers={"Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ModelError("Réponse trop volumineuse")
            value = json.loads(raw)
            if not isinstance(value, dict) or "error" in value:
                raise ModelError("Réponse du serveur invalide")
            return value
        except ModelError:
            raise
        except Exception as exc:
            raise ModelError("Ollama indisponible, délai dépassé ou réponse invalide. Vérifiez le serveur local et le modèle installé.") from exc

    def models(self):
        return [m for m in self.request("/api/tags", timeout=5).get("models", [])
                if not m.get("remote_host") and not m.get("remote_model") and "cloud" not in m.get("name", "").lower()]

    def chat(self, payload):
        return self.request("/api/chat", payload)
