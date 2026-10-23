"""Live disk-based Plan Architect with append-only archive."""

from datetime import datetime
from pathlib import Path


class PlanArch:
    """Manages plans/PLAN-LIVE.md with live focus and append-only archive."""

    @staticmethod
    def init_plan(goal: str, subplans: list[dict[str, str]]) -> dict:
        """Initialize plan data structure."""
        return {
            "goal": goal,
            "active": subplans[0] if subplans else None,
            "pending": subplans[1:] if len(subplans) > 1 else [],
            "archive": [],
        }

    @staticmethod
    def rotate_step(plan: dict, evid: str = "exit_code: 0") -> dict:
        """Move active step to bottom archive and advance focus."""
        if not plan.get("active"):
            return plan

        done_step = dict(plan["active"])
        done_step["done_at"] = datetime.now().isoformat()
        done_step["evidence"] = evid
        plan["archive"].append(done_step)

        if plan.get("pending"):
            plan["active"] = plan["pending"].pop(0)
        else:
            plan["active"] = None

        return plan

    @staticmethod
    def render_md(plan: dict) -> str:
        """Render plan data to Markdown."""
        lines = [
            f"# Живой план (PLAN-LIVE.md)\n",
            f"**Цель:** {plan.get('goal', 'N/A')}\n\n",
            "## 🎯 ТЕКУЩИЙ ФОКУС (Active Subplan)\n",
        ]

        active = plan.get("active")
        if active:
            lines.append(f"* [ ] **{active.get('id')}:** {active.get('title')}\n")
            lines.append(f"  * Бюджет diff: <= {active.get('max_diff', 30)} строк\n\n")
        else:
            lines.append("*Все активные задачи выполнены.*\n\n")

        lines.append("## 🌳 ОСТАВШИЕСЯ ПОДПЛАНЫ\n")
        for p in plan.get("pending", []):
            lines.append(f"* ⏳ **{p.get('id')}:** {p.get('title')}\n")
        lines.append("\n---\n\n## 📜 АРХИВ ВЫПОЛНЕННЫХ ШАГОВ (Не удаляется)\n")

        for a in plan.get("archive", []):
            lines.append(
                f"* [x] **{a.get('id')}:** {a.get('title')}\n"
                f"  * Дата: {a.get('done_at')}\n"
                f"  * Доказательство: `{a.get('evidence')}`\n"
            )
        return "".join(lines)

    @classmethod
    def save_disk(cls, plan: dict, out_p: str = "plans/PLAN-LIVE.md") -> bool:
        """Save rendered plan directly to disk."""
        target = Path(out_p).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(cls.render_md(plan))
            return True
        except OSError:
            return False
