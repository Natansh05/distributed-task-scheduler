from pydantic import BaseModel

class StatusResponse(BaseModel):
    node_id: str
    role: str
    current_token: int | None
    current_leader: str | None
    lease_ttl_remaining: int | None