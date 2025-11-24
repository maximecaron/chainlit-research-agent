import chainlit as cl
from chainlit.data import BaseDataLayer
from chainlit.user import PersistedUser, User
from chainlit.types import ThreadDict
from chainlit.step import StepDict
from chainlit.element import ElementDict
from chainlit.types import Feedback, Pagination, ThreadFilter, PaginatedResponse
from typing import Optional, List, Dict
import uuid

# Helper to create an ID if one doesn't exist
def _get_id(obj: Dict, key: str) -> str:
    if key not in obj:
        obj[key] = str(uuid.uuid4())
    return obj[key]

class InMemoryDataLayer(BaseDataLayer):
    def __init__(self):
        # In-memory storage using dictionaries
        self.users: Dict[str, PersistedUser] = {}
        self.threads: Dict[str, ThreadDict] = {}
        self.steps: Dict[str, StepDict] = {}
        self.elements: Dict[str, ElementDict] = {}
        self.feedback: Dict[str, Feedback] = {}
        
    # --- User Methods ---
    
    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        # User is typically identified by an email or unique username
        return self.users.get(identifier)

    async def create_user(self, user: User) -> Optional[PersistedUser]:
        if user.identifier in self.users:
            return self.users[user.identifier]
        
        # Create a mock PersistedUser object
        persisted_user = PersistedUser(
            id=user.identifier,
            identifier=user.identifier,
            createdAt=cl.utils.make_datetime(),
            metadata=user.metadata or {},
            provider=user.provider,
            role=user.role,
            display_name=user.display_name
        )
        self.users[user.identifier] = persisted_user
        return persisted_user
    
    async def build_debug_url(self) -> str:
        return ""
    
    async def close(self) -> None:
        return
    # --- Thread Methods ---

    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        return self.threads.get(thread_id)

    async def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self.threads:
            del self.threads[thread_id]
            # In a real implementation, you'd also delete associated steps, elements, etc.
            # For this simple in-memory example, we'll keep it simple.
            return True
        return False
    
    async def list_threads(
        self, pagination: Pagination, filters: ThreadFilter
    ) -> PaginatedResponse[ThreadDict]:
        # Simplified listing: only filter by user_id if present
        all_threads = list(self.threads.values())
        
        if filters.userId:
            all_threads = [t for t in all_threads if t["userId"] == filters.userId]
        
        # Simple pagination (no proper sorting/offset, just slicing)
        start = (pagination.page - 1) * pagination.pageSize
        end = start + pagination.pageSize
        
        return PaginatedResponse(
            page=pagination.page,
            pageSize=pagination.pageSize,
            total=len(all_threads),
            data=all_threads[start:end],
        )

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        thread = self.threads.get(thread_id)
        if not thread:
            return False

        if name is not None:
            thread["name"] = name
        if user_id is not None:
            thread["userId"] = user_id
        if metadata is not None:
            thread["metadata"] = metadata
        if tags is not None:
            thread["tags"] = tags

        return True

    # --- Step Methods ---

    async def create_step(self, step_dict: StepDict) -> str:
        step_id = _get_id(step_dict, "id")
        self.steps[step_id] = step_dict
        return step_id

    async def update_step(self, step_dict: StepDict) -> bool:
        if "id" not in step_dict or step_dict["id"] not in self.steps:
            return False
        
        step_id = step_dict["id"]
        # Update the existing step entry with new values
        self.steps[step_id].update(step_dict)
        return True
    
    async def delete_step(self, step_id: str) -> bool:
        if step_id in self.steps:
            del self.steps[step_id]
            return True
        return False

    # --- Other Abstract Methods (Simplified) ---

    async def upsert_feedback(self, feedback: Feedback) -> str:
        # Generate an ID for the feedback
        feedback_id = str(uuid.uuid4())
        # Store a copy of the feedback object
        self.feedback[feedback_id] = feedback
        return feedback_id

    async def delete_feedback(self, feedback_id: str) -> bool:
        if feedback_id in self.feedback:
            del self.feedback[feedback_id]
            return True
        return False

    async def create_element(self, element_dict: ElementDict) -> str:
        element_id = _get_id(element_dict, "id")
        self.elements[element_id] = element_dict
        return element_id

    async def get_element(self, thread_id: str, element_id: str) -> Optional[ElementDict]:
        return self.elements.get(element_id) # Note: ignoring thread_id for simplicity

    async def delete_element(self, element_id: str) -> bool:
        if element_id in self.elements:
            del self.elements[element_id]
            return True
        return False
    
    async def get_thread_author(self, thread_id: str) -> Optional[str]:
        thread = self.threads.get(thread_id)
        return thread.get("userId") if thread else None

    async def delete_user_session(self, id: str) -> bool:
        # Not fully implemented for simple in-memory layer
        return True 

    # --- Custom Method to Simulate Thread Persistence in Chainlit ---
    
    # This is not part of BaseDataLayer but is often needed for testing/mocking 
    # the behavior of how Chainlit saves a new thread.
    async def create_thread(self, thread_dict: ThreadDict) -> str:
        thread_id = _get_id(thread_dict, "id")
        self.threads[thread_id] = thread_dict
        return thread_id