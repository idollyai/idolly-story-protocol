"""Base Agent Class for Idolly Autonomous Agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from agent.story_protocol.client import StoryProtocolClient

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all autonomous agents"""
    
    def __init__(
        self, 
        agent_id: str, 
        story_client: StoryProtocolClient,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for the agent
            story_client: Story Protocol client instance
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.story_client = story_client
        self.config = config or {}
        self.is_active = False
        self.created_at = datetime.utcnow()
        self.last_activity = None
        self.tasks_queue = asyncio.Queue()
        self.execution_history = []
        
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task
        
        Args:
            task: Task dictionary containing task details
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status
        
        Returns:
            Status dictionary
        """
        pass
    
    async def start(self) -> None:
        """Start the agent"""
        logger.info(f"Starting agent: {self.agent_id}")
        self.is_active = True
        self.last_activity = datetime.utcnow()
        
        # Start task execution loop
        asyncio.create_task(self._task_execution_loop())
        
    async def stop(self) -> None:
        """Stop the agent"""
        logger.info(f"Stopping agent: {self.agent_id}")
        self.is_active = False
        
    async def add_task(self, task: Dict[str, Any]) -> None:
        """Add a task to the agent's queue"""
        await self.tasks_queue.put(task)
        logger.debug(f"Task added to agent {self.agent_id}: {task['type']}")
        
    async def _task_execution_loop(self) -> None:
        """Main task execution loop"""
        while self.is_active:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.tasks_queue.get(),
                    timeout=60.0  # 1 minute timeout
                )
                
                # Execute task
                result = await self.execute_task(task)
                
                # Update activity timestamp
                self.last_activity = datetime.utcnow()
                
                # Store in execution history
                self.execution_history.append({
                    "task": task,
                    "result": result,
                    "timestamp": self.last_activity
                })
                
                # Keep history size manageable
                if len(self.execution_history) > 100:
                    self.execution_history = self.execution_history[-100:]
                    
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in agent {self.agent_id} task execution: {str(e)}")
                
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_id": self.agent_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "tasks_in_queue": self.tasks_queue.qsize(),
            "tasks_executed": len(self.execution_history),
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds()
        }