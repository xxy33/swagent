"""
Persistence module for StateGraph workflow engine.
Provides checkpoint storage for workflow state.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from copy import deepcopy
import json
import os
import uuid


@dataclass
class WorkflowCheckpoint:
    """
    Checkpoint data for workflow persistence.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint
        execution_id: Execution run identifier
        graph_name: Name of the graph
        state: State at checkpoint time
        current_node: Current node being executed
        iteration: Current iteration number
        history: Node execution history
        timestamp: When checkpoint was created
        metadata: Additional checkpoint metadata
    """
    checkpoint_id: str
    execution_id: str
    graph_name: str
    state: Dict[str, Any]
    current_node: str
    iteration: int
    history: List[Dict[str, Any]]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        execution_id: str,
        graph_name: str,
        state: Dict[str, Any],
        current_node: str,
        iteration: int,
        history: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "WorkflowCheckpoint":
        """Create a new checkpoint."""
        return cls(
            checkpoint_id=str(uuid.uuid4()),
            execution_id=execution_id,
            graph_name=graph_name,
            state=deepcopy(state),
            current_node=current_node,
            iteration=iteration,
            history=history or [],
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "execution_id": self.execution_id,
            "graph_name": self.graph_name,
            "state": self.state,
            "current_node": self.current_node,
            "iteration": self.iteration,
            "history": self.history,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowCheckpoint":
        """Create checkpoint from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            execution_id=data["execution_id"],
            graph_name=data["graph_name"],
            state=data["state"],
            current_node=data["current_node"],
            iteration=data["iteration"],
            history=data.get("history", []),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class BasePersistence(ABC):
    """
    Abstract base class for persistence backends.

    Implementations should provide thread-safe access to checkpoints.
    """

    @abstractmethod
    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> str:
        """
        Save a checkpoint.

        Args:
            checkpoint: The checkpoint to save

        Returns:
            The checkpoint ID
        """
        pass

    @abstractmethod
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """
        Load a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint ID

        Returns:
            The checkpoint if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_latest_checkpoint(
        self,
        execution_id: str
    ) -> Optional[WorkflowCheckpoint]:
        """
        Get the latest checkpoint for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            The latest checkpoint if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        graph_name: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowCheckpoint]:
        """
        List checkpoints with optional filters.

        Args:
            execution_id: Filter by execution ID
            graph_name: Filter by graph name
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints
        """
        pass

    @abstractmethod
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear_execution(self, execution_id: str) -> int:
        """
        Clear all checkpoints for an execution.

        Args:
            execution_id: The execution ID

        Returns:
            Number of checkpoints deleted
        """
        pass


class MemoryPersistence(BasePersistence):
    """
    In-memory persistence backend.

    Useful for testing and development.
    Data is lost when the process ends.
    """

    def __init__(self):
        self._checkpoints: Dict[str, WorkflowCheckpoint] = {}
        self._by_execution: Dict[str, List[str]] = {}

    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> str:
        """Save checkpoint to memory."""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint

        # Index by execution
        if checkpoint.execution_id not in self._by_execution:
            self._by_execution[checkpoint.execution_id] = []
        self._by_execution[checkpoint.execution_id].append(checkpoint.checkpoint_id)

        return checkpoint.checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Load checkpoint from memory."""
        return self._checkpoints.get(checkpoint_id)

    async def get_latest_checkpoint(
        self,
        execution_id: str
    ) -> Optional[WorkflowCheckpoint]:
        """Get latest checkpoint for execution."""
        checkpoint_ids = self._by_execution.get(execution_id, [])
        if not checkpoint_ids:
            return None

        # Get all checkpoints for this execution
        checkpoints = [
            self._checkpoints[cid] for cid in checkpoint_ids
            if cid in self._checkpoints
        ]

        if not checkpoints:
            return None

        # Return the one with the latest timestamp
        return max(checkpoints, key=lambda c: c.timestamp)

    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        graph_name: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowCheckpoint]:
        """List checkpoints with filters."""
        checkpoints = list(self._checkpoints.values())

        if execution_id:
            checkpoints = [c for c in checkpoints if c.execution_id == execution_id]

        if graph_name:
            checkpoints = [c for c in checkpoints if c.graph_name == graph_name]

        # Sort by timestamp descending
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

        return checkpoints[:limit]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint from memory."""
        if checkpoint_id not in self._checkpoints:
            return False

        checkpoint = self._checkpoints.pop(checkpoint_id)

        # Remove from execution index
        if checkpoint.execution_id in self._by_execution:
            self._by_execution[checkpoint.execution_id] = [
                cid for cid in self._by_execution[checkpoint.execution_id]
                if cid != checkpoint_id
            ]

        return True

    async def clear_execution(self, execution_id: str) -> int:
        """Clear all checkpoints for execution."""
        checkpoint_ids = self._by_execution.pop(execution_id, [])

        for cid in checkpoint_ids:
            self._checkpoints.pop(cid, None)

        return len(checkpoint_ids)

    def clear_all(self) -> None:
        """Clear all checkpoints (for testing)."""
        self._checkpoints.clear()
        self._by_execution.clear()


class LocalFilePersistence(BasePersistence):
    """
    Local file system persistence backend.

    Stores checkpoints as JSON files in a directory.
    """

    def __init__(self, base_dir: str = ".stategraph_checkpoints"):
        """
        Initialize local file persistence.

        Args:
            base_dir: Directory for storing checkpoint files
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _get_file_path(self, checkpoint_id: str) -> str:
        """Get file path for a checkpoint."""
        return os.path.join(self.base_dir, f"{checkpoint_id}.json")

    def _get_execution_dir(self, execution_id: str) -> str:
        """Get directory for an execution's checkpoints."""
        return os.path.join(self.base_dir, "by_execution", execution_id)

    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> str:
        """Save checkpoint to file."""
        # Save main checkpoint file
        file_path = self._get_file_path(checkpoint.checkpoint_id)
        with open(file_path, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        # Create execution index
        exec_dir = self._get_execution_dir(checkpoint.execution_id)
        os.makedirs(exec_dir, exist_ok=True)

        # Create symlink or reference file
        ref_path = os.path.join(exec_dir, f"{checkpoint.checkpoint_id}.ref")
        with open(ref_path, 'w') as f:
            f.write(checkpoint.checkpoint_id)

        return checkpoint.checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Load checkpoint from file."""
        file_path = self._get_file_path(checkpoint_id)

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        return WorkflowCheckpoint.from_dict(data)

    async def get_latest_checkpoint(
        self,
        execution_id: str
    ) -> Optional[WorkflowCheckpoint]:
        """Get latest checkpoint for execution."""
        exec_dir = self._get_execution_dir(execution_id)

        if not os.path.exists(exec_dir):
            return None

        # Get all checkpoint references
        ref_files = [f for f in os.listdir(exec_dir) if f.endswith('.ref')]

        if not ref_files:
            return None

        # Load all checkpoints and find the latest
        latest = None
        latest_time = None

        for ref_file in ref_files:
            ref_path = os.path.join(exec_dir, ref_file)
            with open(ref_path, 'r') as f:
                checkpoint_id = f.read().strip()

            checkpoint = await self.load_checkpoint(checkpoint_id)
            if checkpoint:
                if latest is None or checkpoint.timestamp > latest_time:
                    latest = checkpoint
                    latest_time = checkpoint.timestamp

        return latest

    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        graph_name: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowCheckpoint]:
        """List checkpoints with filters."""
        checkpoints = []

        if execution_id:
            # List from specific execution directory
            exec_dir = self._get_execution_dir(execution_id)
            if os.path.exists(exec_dir):
                ref_files = [f for f in os.listdir(exec_dir) if f.endswith('.ref')]
                for ref_file in ref_files:
                    ref_path = os.path.join(exec_dir, ref_file)
                    with open(ref_path, 'r') as f:
                        checkpoint_id = f.read().strip()
                    checkpoint = await self.load_checkpoint(checkpoint_id)
                    if checkpoint:
                        if graph_name is None or checkpoint.graph_name == graph_name:
                            checkpoints.append(checkpoint)
        else:
            # List all checkpoints
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    checkpoint_id = filename[:-5]  # Remove .json
                    checkpoint = await self.load_checkpoint(checkpoint_id)
                    if checkpoint:
                        if graph_name is None or checkpoint.graph_name == graph_name:
                            checkpoints.append(checkpoint)

        # Sort by timestamp descending
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

        return checkpoints[:limit]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint file."""
        file_path = self._get_file_path(checkpoint_id)

        if not os.path.exists(file_path):
            return False

        # Load to get execution_id
        checkpoint = await self.load_checkpoint(checkpoint_id)

        # Remove main file
        os.remove(file_path)

        # Remove reference file
        if checkpoint:
            ref_path = os.path.join(
                self._get_execution_dir(checkpoint.execution_id),
                f"{checkpoint_id}.ref"
            )
            if os.path.exists(ref_path):
                os.remove(ref_path)

        return True

    async def clear_execution(self, execution_id: str) -> int:
        """Clear all checkpoints for execution."""
        exec_dir = self._get_execution_dir(execution_id)
        count = 0

        if not os.path.exists(exec_dir):
            return 0

        ref_files = [f for f in os.listdir(exec_dir) if f.endswith('.ref')]

        for ref_file in ref_files:
            ref_path = os.path.join(exec_dir, ref_file)
            with open(ref_path, 'r') as f:
                checkpoint_id = f.read().strip()

            # Delete main file
            file_path = self._get_file_path(checkpoint_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                count += 1

            # Delete reference
            os.remove(ref_path)

        # Try to remove empty execution directory
        try:
            os.rmdir(exec_dir)
        except OSError:
            pass  # Directory not empty or other error

        return count

    def clear_all(self) -> None:
        """Clear all checkpoints (for testing)."""
        import shutil
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
