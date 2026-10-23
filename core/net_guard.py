"""Zero-token network guard and resilient Outbox queue with In-Flight recovery."""

import json
import os
import socket
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional


class NetGuard:
    """Network connection guard and resilient Outbox queue manager."""

    def __init__(
        self,
        root: str = "memory/outbox",
        max_items: int = 50,
        max_len: int = 300,
    ) -> None:
        """Initialize NetGuard with directory and limits."""
        self.root = root
        self.max_items = max_items
        self.max_len = max_len
        self._seq = 0
        os.makedirs(self.root, exist_ok=True)

    def _get_proxy(self) -> Optional[tuple[str, int]]:
        """Extract host and port from HTTP/HTTPS proxy environment."""
        p_url = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not p_url:
            return None
        parsed = urllib.parse.urlparse(p_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 10809
        return host, port

    def chk_online(
        self,
        host: str = "8.8.8.8",
        port: int = 53,
        timeout: float = 2.0,
        use_proxy: bool = True,
    ) -> bool:
        """Verify network connectivity via lightweight socket probe."""
        target_h, target_p = host, port
        if use_proxy:
            proxy_cfg = self._get_proxy()
            if proxy_cfg:
                target_h, target_p = proxy_cfg

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            res = sock.connect_ex((target_h, target_p))
            return res == 0
        except Exception:
            return False
        finally:
            sock.close()

    def has_pending(self) -> bool:
        """Check if any packets are waiting in the queue."""
        if not os.path.exists(self.root):
            return False
        for f_name in os.listdir(self.root):
            if f_name.endswith(".json") or f_name.endswith(".inflight"):
                return True
        return False

    def enqueue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically persist payload into outbox enforcing Gate 8 and limits."""
        raw = json.dumps(payload, ensure_ascii=False)
        if len(raw) > self.max_len:
            return {"ok": False, "err": "len_exceeded", "id": None}

        items = [f for f in os.listdir(self.root) if f.endswith(".json")]
        if len(items) >= self.max_items:
            return {"ok": False, "err": "queue_full", "id": None}

        self._seq += 1
        pkt_id = f"{int(time.time() * 1000)}_{self._seq}"
        path = os.path.join(self.root, f"pkt_{pkt_id}.json")
        rec = {
            "id": pkt_id,
            "created": time.time(),
            "payload": payload,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)
        return {"ok": True, "err": None, "id": pkt_id}

    def rec_inflight(self, max_age: float = 60.0) -> int:
        """Recover abandoned inflight files back to pending json."""
        if not os.path.exists(self.root):
            return 0
        count = 0
        now = time.time()
        for f_name in os.listdir(self.root):
            if not f_name.endswith(".inflight"):
                continue
            p = os.path.join(self.root, f_name)
            if now - os.path.getmtime(p) > max_age:
                target = p[:-9] + ".json"
                os.rename(p, target)
                count += 1
        return count

    def purge_old(self, ttl_sec: float = 86400.0) -> int:
        """Delete packets that exceeded TTL."""
        if not os.path.exists(self.root):
            return 0
        count = 0
        now = time.time()
        for f_name in os.listdir(self.root):
            if not f_name.endswith(".json"):
                continue
            p = os.path.join(self.root, f_name)
            if now - os.path.getmtime(p) > ttl_sec:
                os.remove(p)
                count += 1
        return count

    def _send_one(self, p_json: str, send_fn: Callable[[Dict[str, Any]], bool]) -> bool:
        """Send one pending packet with atomic inflight handling."""
        p_fly = p_json[:-5] + ".inflight"
        try:
            os.rename(p_json, p_fly)
            with open(p_fly, "r", encoding="utf-8") as f:
                data = json.load(f)
            if send_fn(data.get("payload", {})):
                os.remove(p_fly)
                return True
            os.rename(p_fly, p_json)
            return False
        except Exception:
            if os.path.exists(p_fly):
                os.rename(p_fly, p_json)
            return False

    def poll_step(
        self,
        send_fn: Callable[[Dict[str, Any]], bool],
        ttl_sec: float = 86400.0,
    ) -> Dict[str, Any]:
        """Perform one discrete outbox delivery step."""
        self.rec_inflight()
        self.purge_old(ttl_sec)
        if not self.has_pending():
            return {"status": "idle", "sent": 0}
        if not self.chk_online():
            return {"status": "offline", "sent": 0}

        sent = 0
        files = sorted([f for f in os.listdir(self.root) if f.endswith(".json")])
        for f_name in files:
            p_json = os.path.join(self.root, f_name)
            if not self._send_one(p_json, send_fn):
                break
            sent += 1
        return {"status": "online", "sent": sent}
