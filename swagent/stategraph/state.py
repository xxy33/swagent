"""
State management for StateGraph workflow engine.
Provides state types, snapshots, and state management utilities.
"""
from dataclasses import dataclass, field
from typing import TypedDict, Dict, Any, List, Optional, Type, Callable, Union
from enum import Enum
from datetime import datetime
from copy import deepcopy
import uuid


class MergeStrategy(Enum):
    """State merge strategies for combining state updates."""
    OVERWRITE = "overwrite"  # Replace existing value entirely
    APPEND = "append"        # Append to list/string
    MERGE = "merge"          # Deep merge for dicts
    KEEP = "keep"            # Keep existing value, ignore new


# Type alias for state type
StateType = TypedDict


@dataclass
class StateSnapshot:
    """
    Immutable snapshot of state at a point in time.
    Used for history tracking and rollback functionality.
    """
    snapshot_id: str
    state: Dict[str, Any]
    timestamp: datetime
    node_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        state: Dict[str, Any],
        node_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "StateSnapshot":
        """Create a new snapshot from current state."""
        return cls(
            snapshot_id=str(uuid.uuid4()),
            state=deepcopy(state),
            timestamp=datetime.now(),
            node_name=node_name,
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "node_name": self.node_name,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """Create snapshot from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            state=data["state"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            node_name=data.get("node_name"),
            metadata=data.get("metadata", {})
        )


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        updates: Updates to apply

    Returns:
        Merged dictionary
    """
    result = deepcopy(base)
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _apply_merge_strategy(
    existing: Any,
    new_value: Any,
    strategy: MergeStrategy
) -> Any:
    """
    Apply merge strategy to combine existing and new values.

    Args:
        existing: Existing value in state
        new_value: New value to merge
        strategy: Merge strategy to apply

    Returns:
        Merged value
    """
    if strategy == MergeStrategy.OVERWRITE:
        return deepcopy(new_value)

    elif strategy == MergeStrategy.KEEP:
        return existing if existing is not None else deepcopy(new_value)

    elif strategy == MergeStrategy.APPEND:
        if existing is None:
            return deepcopy(new_value)
        if isinstance(existing, list) and isinstance(new_value, list):
            return existing + deepcopy(new_value)
        if isinstance(existing, str) and isinstance(new_value, str):
            return existing + new_value
        # Fall back to overwrite for incompatible types
        return deepcopy(new_value)

    elif strategy == MergeStrategy.MERGE:
        if existing is None:
            return deepcopy(new_value)
        if isinstance(existing, dict) and isinstance(new_value, dict):
            return _deep_merge(existing, new_value)
        # Fall back to overwrite for non-dict types
        return deepcopy(new_value)

    return deepcopy(new_value)


class StateManager:
    """
    Manages state lifecycle including reads, writes, history, and rollback.

    Attributes:
        state_type: The TypedDict class defining the state schema
        state: Current state dictionary
        history: List of state snapshots
        merge_strategies: Per-field merge strategies
    """

    def __init__(
        self,
        state_type: Optional[Type[StateType]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        max_history: int = 100,
        default_merge_strategy: MergeStrategy = MergeStrategy.OVERWRITE
    ):
        """
        Initialize state manager.

        Args:
            state_type: TypedDict class defining state schema (optional)
            initial_state: Initial state values
            max_history: Maximum number of snapshots to keep
            default_merge_strategy: Default strategy for merging state updates
        """
        self.state_type = state_type
        self._state: Dict[str, Any] = {}
        self._history: List[StateSnapshot] = []
        self._max_history = max_history
        self._default_merge_strategy = default_merge_strategy
        self._field_strategies: Dict[str, MergeStrategy] = {}

        # Initialize with type defaults if available
        if state_type is not None:
            annotations = getattr(state_type, "__annotations__", {})
            for key in annotations:
                self._state[key] = None

        # Apply initial state
        if initial_state:
            self._state.update(deepcopy(initial_state))

    @property
    def state(self) -> Dict[str, Any]:
        """Get current state (read-only copy)."""
        return deepcopy(self._state)

    @property
    def history(self) -> List[StateSnapshot]:
        """Get state history (read-only copy)."""
        return list(self._history)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        value = self._state.get(key, default)
        return deepcopy(value) if value is not None else default

    def set(
        self,
        key: str,
        value: Any,
        strategy: Optional[MergeStrategy] = None,
        save_snapshot: bool = False,
        node_name: Optional[str] = None
    ) -> None:
        """
        Set a value in state.

        Args:
            key: State key
            value: Value to set
            strategy: Merge strategy (uses field or default strategy if not specified)
            save_snapshot: Whether to save a snapshot before update
            node_name: Node name for snapshot metadata
        """
        if save_snapshot:
            self.save_snapshot(node_name=node_name)

        # Determine merge strategy
        if strategy is None:
            strategy = self._field_strategies.get(key, self._default_merge_strategy)

        existing = self._state.get(key)
        self._state[key] = _apply_merge_strategy(existing, value, strategy)

    def update(
        self,
        updates: Dict[str, Any],
        strategy: Optional[MergeStrategy] = None,
        save_snapshot: bool = False,
        node_name: Optional[str] = None
    ) -> None:
        """
        Update multiple values in state.

        Args:
            updates: Dictionary of updates
            strategy: Merge strategy to use for all updates
            save_snapshot: Whether to save a snapshot before update
            node_name: Node name for snapshot metadata
        """
        if save_snapshot:
            self.save_snapshot(node_name=node_name)

        for key, value in updates.items():
            key_strategy = strategy or self._field_strategies.get(key, self._default_merge_strategy)
            existing = self._state.get(key)
            self._state[key] = _apply_merge_strategy(existing, value, key_strategy)

    def set_merge_strategy(self, key: str, strategy: MergeStrategy) -> None:
        """
        Set merge strategy for a specific field.

        Args:
            key: State key
            strategy: Merge strategy to use
        """
        self._field_strategies[key] = strategy

    def save_snapshot(
        self,
        node_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateSnapshot:
        """
        Save current state as a snapshot.

        Args:
            node_name: Name of node that triggered snapshot
            metadata: Additional metadata

        Returns:
            Created snapshot
        """
        snapshot = StateSnapshot.create(
            state=self._state,
            node_name=node_name,
            metadata=metadata
        )
        self._history.append(snapshot)

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return snapshot

    def rollback(self, snapshot_id: Optional[str] = None, steps: int = 1) -> bool:
        """
        Rollback state to a previous snapshot.

        Args:
            snapshot_id: Specific snapshot ID to rollback to
            steps: Number of steps to rollback (ignored if snapshot_id provided)

        Returns:
            True if rollback successful, False otherwise
        """
        if not self._history:
            return False

        if snapshot_id:
            # Find specific snapshot
            for i, snapshot in enumerate(self._history):
                if snapshot.snapshot_id == snapshot_id:
                    self._state = deepcopy(snapshot.state)
                    # Remove snapshots after this one
                    self._history = self._history[:i + 1]
                    return True
            return False
        else:
            # Rollback by steps
            if steps > len(self._history):
                return False

            target_index = len(self._history) - steps
            if target_index < 0:
                return False

            snapshot = self._history[target_index]
            self._state = deepcopy(snapshot.state)
            self._history = self._history[:target_index + 1]
            return True

    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """
        Get a specific snapshot by ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot if found, None otherwise
        """
        for snapshot in self._history:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None

    def clear_history(self) -> None:
        """Clear all history snapshots."""
        self._history.clear()

    def reset(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        """
        Reset state to initial values.

        Args:
            initial_state: New initial state (optional)
        """
        self._state.clear()
        self._history.clear()

        # Initialize with type defaults if available
        if self.state_type is not None:
            annotations = getattr(self.state_type, "__annotations__", {})
            for key in annotations:
                self._state[key] = None

        if initial_state:
            self._state.update(deepcopy(initial_state))

    def validate(self) -> List[str]:
        """
        Validate current state against state type.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.state_type is None:
            return errors

        annotations = getattr(self.state_type, "__annotations__", {})
        required_keys = getattr(self.state_type, "__required_keys__", set(annotations.keys()))

        # Check for missing required keys
        for key in required_keys:
            if key not in self._state or self._state[key] is None:
                errors.append(f"Missing required field: {key}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize state manager to dictionary.

        Returns:
            Serialized state manager
        """
        return {
            "state": deepcopy(self._state),
            "history": [s.to_dict() for s in self._history],
            "field_strategies": {k: v.value for k, v in self._field_strategies.items()},
            "default_merge_strategy": self._default_merge_strategy.value
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        state_type: Optional[Type[StateType]] = None
    ) -> "StateManager":
        """
        Deserialize state manager from dictionary.

        Args:
            data: Serialized state manager
            state_type: State type class

        Returns:
            StateManager instance
        """
        manager = cls(
            state_type=state_type,
            default_merge_strategy=MergeStrategy(data.get("default_merge_strategy", "overwrite"))
        )
        manager._state = deepcopy(data.get("state", {}))
        manager._history = [
            StateSnapshot.from_dict(s) for s in data.get("history", [])
        ]
        manager._field_strategies = {
            k: MergeStrategy(v) for k, v in data.get("field_strategies", {}).items()
        }
        return manager

    def __repr__(self) -> str:
        return f"<StateManager(keys={list(self._state.keys())}, history={len(self._history)})>"
