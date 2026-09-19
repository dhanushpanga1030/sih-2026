"""Government Workflow State Machine.

Manages the lifecycle of risk assessments and relocation decisions
through AI recommendation -> Officer review -> Approval -> Action.
"""
from datetime import datetime
from enum import Enum


class WorkflowState(str, Enum):
    AI_RECOMMENDATION = "ai_recommendation"
    OFFICER_REVIEW = "officer_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS = {
    WorkflowState.AI_RECOMMENDATION: [WorkflowState.OFFICER_REVIEW, WorkflowState.APPROVED, WorkflowState.REJECTED],
    WorkflowState.OFFICER_REVIEW: [WorkflowState.APPROVED, WorkflowState.REJECTED, WorkflowState.MODIFIED],
    WorkflowState.MODIFIED: [WorkflowState.OFFICER_REVIEW, WorkflowState.APPROVED],
    WorkflowState.APPROVED: [WorkflowState.IN_PROGRESS, WorkflowState.CANCELLED],
    WorkflowState.IN_PROGRESS: [WorkflowState.COMPLETED, WorkflowState.CANCELLED],
    WorkflowState.REJECTED: [WorkflowState.AI_RECOMMENDATION],
    WorkflowState.COMPLETED: [],
    WorkflowState.CANCELLED: [WorkflowState.AI_RECOMMENDATION],
}


class WorkflowItem:
    """Single workflow tracking item."""

    def __init__(self, item_id: str, item_type: str, habitation: str, data: dict):
        self.item_id = item_id
        self.item_type = item_type  # "risk_assessment", "relocation_plan", "emergency_response"
        self.habitation = habitation
        self.state = WorkflowState.AI_RECOMMENDATION
        self.data = data
        self.history = [{
            "state": WorkflowState.AI_RECOMMENDATION,
            "timestamp": datetime.utcnow().isoformat(),
            "actor": "system",
            "note": "AI recommendation generated",
        }]
        self.assigned_officer = None
        self.officer_notes = None

    def transition(self, new_state: WorkflowState, actor: str, note: str = "") -> bool:
        if new_state not in VALID_TRANSITIONS.get(self.state, []):
            return False

        self.state = new_state
        self.history.append({
            "state": new_state,
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "note": note,
        })

        if new_state == WorkflowState.OFFICER_REVIEW and not self.assigned_officer:
            self.assigned_officer = actor
        if new_state == WorkflowState.MODIFIED:
            self.officer_notes = note

        return True

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "habitation": self.habitation,
            "state": self.state,
            "data": self.data,
            "history": self.history,
            "assigned_officer": self.assigned_officer,
            "officer_notes": self.officer_notes,
        }


class WorkflowManager:
    """Manage all workflow items."""

    def __init__(self):
        self._items: dict[str, WorkflowItem] = {}
        self._counter = 0

    def create(self, item_type: str, habitation: str, data: dict) -> dict:
        self._counter += 1
        item_id = f"WF-{self._counter:04d}"
        item = WorkflowItem(item_id, item_type, habitation, data)
        self._items[item_id] = item
        return item.to_dict()

    def get(self, item_id: str) -> dict | None:
        item = self._items.get(item_id)
        return item.to_dict() if item else None

    def list_items(self, state: str = None, item_type: str = None) -> list:
        items = list(self._items.values())
        if state:
            items = [i for i in items if i.state == state]
        if item_type:
            items = [i for i in items if i.item_type == item_type]
        return [i.to_dict() for i in sorted(items, key=lambda x: x.history[-1]["timestamp"], reverse=True)]

    def transition(self, item_id: str, new_state: str, actor: str, note: str = "") -> dict:
        item = self._items.get(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}

        state = WorkflowState(new_state)
        success = item.transition(state, actor, note)
        if not success:
            return {"error": f"Invalid transition from {item.state} to {new_state}"}
        return item.to_dict()

    def stats(self) -> dict:
        states = {}
        for item in self._items.values():
            states[item.state] = states.get(item.state, 0) + 1
        return {
            "total": len(self._items),
            "by_state": states,
            "pending_review": states.get(WorkflowState.OFFICER_REVIEW, 0),
            "completed": states.get(WorkflowState.COMPLETED, 0),
        }


workflow_manager = WorkflowManager()
