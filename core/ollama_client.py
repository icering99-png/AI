"""Local Ollama client with lifecycle and VRAM headroom management."""
import json
import os
import re
import socket
import subprocess
import threading
import urllib.request
from typing import Any, Dict, List, Optional


class OllamaClient:
    """Zero-cloud token client with single-instance and VRAM controls."""

    _srv_lock = threading.Lock()
    DEFAULT_SYS = "Write valid Python code. Follow all rules. Do not write text."

    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5-coder:1.5b",
        min_vram_mib: int = 3000,
        min_ram_mib: int = 2048,
        max_cpu_pct: float = 85.0,
        num_gpu: int = 20,
        num_thread: int = 4,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.min_vram_mib = min_vram_mib
        self.min_ram_mib = min_ram_mib
        self.max_cpu_pct = max_cpu_pct
        self.num_gpu = num_gpu
        self.num_thread = num_thread
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def is_alive(self) -> bool:
        """Check if local server port is accepting connections."""
        try:
            with socket.create_connection(("127.0.0.1", 11434), timeout=1):
                return True
        except OSError:
            return False

    def ensure_srv(self) -> bool:
        """Start daemon on demand if not already running."""
        if self.is_alive():
            return True
        if os.getenv("NO_AUTOSPAWN") == "1":
            return False
        with self._srv_lock:
            if self.is_alive():
                return True
            os.makedirs("logs", exist_ok=True)
            env = os.environ.copy()
            env["OLLAMA_MODELS"] = os.getenv("OLLAMA_MODELS", r"G:\AI\Ollama\models")
            env["OLLAMA_HOST"] = "127.0.0.1:11434"
            flags = 0x08000000 if os.name == "nt" else 0
            ollama_bin = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
            cmd = [ollama_bin if os.path.exists(ollama_bin) else "ollama", "serve"]
            with open("logs/ollama_srv.log", "a", encoding="utf-8") as log_f:
                self._srv_proc = subprocess.Popen(
                    cmd,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log_f,
                    stderr=log_f,
                    creationflags=flags,
                )
            for _ in range(10):
                if self.is_alive():
                    return True
        return False

    def get_free_ram(self) -> int:
        """Return available system RAM in MiB."""
        try:
            import psutil
            return int(psutil.virtual_memory().available / (1024 * 1024))
        except Exception:
            return 4096

    def get_cpu_pct(self) -> float:
        """Return system CPU usage percentage."""
        try:
            import psutil
            return float(psutil.cpu_percent(interval=None))
        except Exception:
            return 0.0

    def chk_resources(self) -> tuple[bool, str]:
        """Verify GPU VRAM, CPU load, and RAM before inference."""
        vram = self.get_free_vram()
        if vram < self.min_vram_mib:
            return False, f"INSUFFICIENT_VRAM: {vram}MiB < {self.min_vram_mib}MiB"
        ram = self.get_free_ram()
        if ram < self.min_ram_mib:
            return False, f"INSUFFICIENT_RAM: {ram}MiB < {self.min_ram_mib}MiB"
        cpu = self.get_cpu_pct()
        if cpu > self.max_cpu_pct:
            return False, f"CPU_THROTTLED: {cpu}% > {self.max_cpu_pct}%"
        return True, "OK"

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        keep_alive: str = "5m",
        fmt: Optional[str] = None,
    ) -> str:
        """Call local Ollama /api/generate with resource guard."""
        ok_res, res_msg = self.chk_resources()
        if not ok_res:
            raise RuntimeError(f"RESOURCE_GUARD: {res_msg}")
        self.ensure_srv()
        url = f"{self.host}/api/generate"
        sys_prompt = system or self.DEFAULT_SYS
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive,
            "system": sys_prompt,
            "options": {
                "num_gpu": self.num_gpu,
                "num_thread": self.num_thread,
            },
        }
        if fmt:
            payload["format"] = fmt
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with self.opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = str(data.get("response", "")).strip()
            clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            if fmt:
                return clean
            return self.strip_code(clean)

    @staticmethod
    def strip_code(text: str) -> str:
        """Strip markdown fences and preambles from model code output."""
        m = re.search(r"```(?:[a-zA-Z0-9_\-\+]+)?\r?\n(.*?)\r?\n```", text, flags=re.DOTALL)
        if m:
            return m.group(1).strip()
        return text.strip()

    def gen_json(
        self, prompt: str, keys: Optional[List[str]] = None, sys: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON and validate required schema keys."""
        raw = self.generate(prompt=prompt, system=sys, fmt="json")
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        try:
            val = json.loads(clean)
            if not isinstance(val, dict):
                return {"ok": False, "data": None, "err": "not_dict"}
            if keys:
                miss = [k for k in keys if k not in val]
                if miss:
                    return {"ok": False, "data": None, "err": f"miss: {miss}"}
            return {"ok": True, "data": val, "err": None}
        except Exception as exc:
            return {"ok": False, "data": None, "err": str(exc)}

    def translate(self, text: str) -> str:
        """Translate English to Russian using local model."""
        sys_p = "You are a translator. Translate English to Russian. Output translation only."
        return self.generate(prompt=text, system=sys_p)

    def get_loaded(self) -> List[str]:
        """List models currently loaded in GPU VRAM."""
        if not self.is_alive():
            return []
        url = f"{self.host}/api/ps"
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    def get_free_vram(self) -> int:
        """Return free GPU VRAM in MiB using nvidia-smi, or fallback."""
        try:
            cmd = ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"]
            flags = 0x08000000 if os.name == "nt" else 0
            out = subprocess.check_output(cmd, creationflags=flags, text=True).strip()
            return int(out.split("\n")[0])
        except Exception:
            return 4000

    def unload(self, model: Optional[str] = None) -> bool:
        """Evict model from GPU VRAM immediately."""
        target = model or self.model
        url = f"{self.host}/api/generate"
        payload = {"model": target, "keep_alive": 0}
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with self.opener.open(req, timeout=10):
                return True
        except Exception:
            return False
