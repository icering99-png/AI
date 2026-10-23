"""Subplan Decomposer ensuring <= 30 lines diff budget."""


class SubplanDec:
    """Decomposes tasks into atomic DAG subplans with diff limit <= 30."""

    @staticmethod
    def make_subplan(
        idx: int, title: str, max_diff: int = 15, dep: str | None = None
    ) -> dict[str, str | int | None]:
        """Create single quantized subplan node with dependency."""
        sub_id = f"SUB-{idx:02d}"
        clean_title = title.strip()[:60]
        return {
            "id": sub_id,
            "title": clean_title,
            "max_diff": min(max_diff, 30),
            "depends_on": dep,
            "status": "PENDING",
        }

    @classmethod
    def decompose(cls, tasks: list[str]) -> list[dict[str, str | int | None]]:
        """Quantize list of intentions into atomic subplans with sequential DAG."""
        subplans = []
        prev_id = None
        for idx, task in enumerate(tasks, start=1):
            if not task.strip():
                continue
            item = cls.make_subplan(idx, task, dep=prev_id)
            subplans.append(item)
            prev_id = item["id"]
        return subplans

    @staticmethod
    def validate_dag(subplans: list[dict]) -> tuple[bool, str]:
        """Verify subplans limits and topological dependency ordering."""
        seen = set()
        for s in subplans:
            sid = str(s.get("id", ""))
            diff = int(s.get("max_diff", 0))
            if len(sid) > 15:
                return False, f"ID {sid} > 15 chars"
            if diff > 30:
                return False, f"Diff {diff} > 30 lines"
            dep = s.get("depends_on")
            if dep and dep not in seen:
                return False, f"Broken DAG: {sid} depends on unseen {dep}"
            seen.add(sid)
        return True, "DAG OK"

    @classmethod
    def fission_step(cls, sub: dict) -> tuple[dict, dict]:
        """Split stuck subplan into two atomic steps with word-boundary trim."""
        sid = str(sub.get("id", "SUB-01"))
        ttl = str(sub.get("title", "Task")).strip()
        if len(ttl) > 30:
            ttl = ttl[:30].rsplit(" ", 1)[0]
        dep = sub.get("depends_on")
        sub_a = {
            "id": f"{sid}a"[:15],
            "title": f"Part 1: Interface of {ttl}",
            "max_diff": 15,
            "depends_on": dep,
            "status": "PENDING",
        }
        sub_b = {
            "id": f"{sid}b"[:15],
            "title": f"Part 2: Logic of {ttl}",
            "max_diff": 15,
            "depends_on": sub_a["id"],
            "status": "PENDING",
        }
        return sub_a, sub_b
