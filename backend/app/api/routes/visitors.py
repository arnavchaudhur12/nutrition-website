from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.visitor_service import VisitorPresenceService

router = APIRouter()


class VisitorHeartbeatPayload(BaseModel):
    session_id: str


def get_visitor_service(request: Request) -> VisitorPresenceService:
    return request.app.state.visitor_presence_service


@router.get("")
def get_active_visitors(request: Request) -> dict[str, int]:
    return get_visitor_service(request).snapshot()


@router.post("/connect")
def connect_visitor(request: Request) -> dict[str, object]:
    return get_visitor_service(request).connect()


@router.post("/heartbeat")
def heartbeat_visitor(payload: VisitorHeartbeatPayload, request: Request) -> dict[str, object]:
    return get_visitor_service(request).heartbeat(payload.session_id)


@router.post("/disconnect")
def disconnect_visitor(payload: VisitorHeartbeatPayload, request: Request) -> dict[str, int]:
    return get_visitor_service(request).disconnect(payload.session_id)
