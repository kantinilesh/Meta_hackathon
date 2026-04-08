from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio, uuid, os, secrets, logging, time
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import httpx

from .models import (
    NegotiationSession, PartyConfig, SessionStatus, Observation, 
    Action, Reward, TaskConfig, GradeResult, NegotiationTurn, NegotiationRole
)
from .env import ContractEnv
from .dual_env import DualAgentEnv
from .agent_runner import AgentRunner
from .contracts.nda_template import TASK_CONTRACTS, load_contract

app = FastAPI(title="ContractEnv", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

env_sessions: Dict[str, ContractEnv] = {}
negotiation_sessions: Dict[str, NegotiationSession] = {}
ws_connections: Dict[str, List[WebSocket]] = {}

import os
from dotenv import load_dotenv
load_dotenv()
try:
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"), base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1"))
except:
    openai_client = None

# STANDARD OPENENV ENDPOINTS
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "timestamp": time.time(), "active_sessions": len(negotiation_sessions)}

class ResetReq(BaseModel):
    task_id: str
    session_id: Optional[str] = None

@app.post("/reset")
def reset(req: ResetReq):
    session_id = req.session_id or str(uuid.uuid4())
    env = ContractEnv(task_id=req.task_id)
    obs = env.reset()
    env_sessions[session_id] = env
    return {"observation": obs.model_dump(), "session_id": session_id}

class StepReq(BaseModel):
    session_id: str
    action: Action

@app.post("/step")
def step(req: StepReq):
    if req.session_id not in env_sessions:
        raise HTTPException(404, "Session not found")
    obs, reward, done, info = env_sessions[req.session_id].step(req.action)
    return {"observation": obs.model_dump(), "reward": reward.model_dump(), "done": done, "info": info}

@app.get("/state")
def state(session_id: str):
    if session_id not in env_sessions:
        raise HTTPException(404, "Session not found")
    return env_sessions[session_id].state()

@app.get("/tasks")
def tasks():
    return [
        TaskConfig(task_id="task1", name="Clause Identification", difficulty="easy", description="", max_turns=20, target_score=0.85),
        TaskConfig(task_id="task2", name="Clause Redlining", difficulty="medium", description="", max_turns=30, target_score=0.65),
        TaskConfig(task_id="task3", name="Full Negotiation", difficulty="hard", description="", max_turns=50, target_score=0.45),
    ]

# SESSION PRODUCT ENDPOINTS
class SessionCreateReq(BaseModel):
    contract_id: str = "nda_001"
    seller_company_name: str
    seller_constraints: List[dict]
    seller_agent_style: str = "balanced"
    seller_context: str = ""

@app.post("/session/create")
def session_create(req: SessionCreateReq):
    session_id = str(uuid.uuid4())
    invite_token = secrets.token_urlsafe(16)
    
    contract_data = load_contract("task3") # Base contract
    
    seller_config = PartyConfig(
        role="seller",
        company_name=req.seller_company_name,
        constraints=req.seller_constraints,
        agent_style=req.seller_agent_style,
        constraint_summary="Custom constraints",
        company_context=req.seller_context
    )
    
    session = NegotiationSession(
        session_id=session_id,
        status="waiting_client",
        seller_config=seller_config,
        contract_id=req.contract_id,
        contract_title=contract_data["title"],
        clauses=contract_data["clauses"],
        created_at=str(time.time()),
        invite_token=invite_token
    )
    negotiation_sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "invite_token": invite_token,
        "invite_url": f"http://localhost:3000/join/{invite_token}",
        "status": session.status
    }

class SessionJoinReq(BaseModel):
    invite_token: str
    client_company_name: str
    client_constraints: List[dict]
    client_agent_style: str = "balanced"
    client_context: str = ""

@app.post("/session/join")
def session_join(req: SessionJoinReq):
    session = next((s for s in negotiation_sessions.values() if s.invite_token == req.invite_token), None)
    if not session:
        raise HTTPException(404, "Invalid token")
        
    session.client_config = PartyConfig(
        role="client",
        company_name=req.client_company_name,
        constraints=req.client_constraints,
        agent_style=req.client_agent_style,
        constraint_summary="Custom constraints",
        company_context=req.client_context
    )
    session.status = "ready"
    return {"session_id": session.session_id, "status": session.status}

class GradeReq(BaseModel):
    session_id: str
    task_id: str

@app.post("/grade")
def grade(req: GradeReq):
    env = env_sessions.get(req.session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    
    score = sum(t.reward_delta for t in env.history if getattr(t, 'reward_delta', None)) if env.history else 0
    passed = score > 0
    
    return {
        "task_id": req.task_id, 
        "score": score, 
        "breakdown": {}, 
        "passed": passed, 
        "details": ["Grading complete based on accumulated reward."]
    }

class SessionStartReq(BaseModel):
    session_id: str

@app.post("/session/start")
async def session_start(req: SessionStartReq):
    if req.session_id not in negotiation_sessions:
        raise HTTPException(404, "Session not found")
    session = negotiation_sessions[req.session_id]
    session.status = "negotiating"
    
    # Launch background negotiation
    asyncio.create_task(run_negotiation(req.session_id))
    
    return {"session_id": req.session_id, "status": "negotiating", "websocket_url": f"ws://localhost:7860/ws/{req.session_id}"}

class SessionSignReq(BaseModel):
    session_id: str
    role: str

@app.post("/session/sign")
def session_sign(req: SessionSignReq):
    if req.session_id not in negotiation_sessions:
        raise HTTPException(404, "Session not found")
    session = negotiation_sessions[req.session_id]
    if req.role == "seller":
        session.seller_signed = True
    else:
        session.client_signed = True
    return {"status": "signed"}

@app.get("/session/contract")
def session_contract(session_id: str):
    if session_id not in negotiation_sessions:
        raise HTTPException(404, "Session not found")
    session = negotiation_sessions[session_id]
    
    # Rebuild final contract text
    final_text = ""
    for c in session.clauses:
        final_text += f"{c.title}:\n{session.final_agreed_clauses.get(c.id, c.text)}\n\n"
        
    return {"final_contract_text": final_text}
@app.get("/session/status")
def session_status(session_id: str = None, invite_token: str = None, role: str = None):
    session = None
    if session_id:
        session = negotiation_sessions.get(session_id)
    elif invite_token:
        session = next((s for s in negotiation_sessions.values() if s.invite_token == invite_token), None)
        
    if not session:
        raise HTTPException(404, "Session not found")
        
    # Strip opposing party config
    out = session.model_dump()
    if role == "seller":
        out["client_config"] = None
    elif role == "client":
        out["seller_config"] = None
        
    return out

@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str, role: str = "both"):
    await websocket.accept()
    if session_id not in ws_connections:
        ws_connections[session_id] = []
    ws_connections[session_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_connections[session_id].remove(websocket)

async def broadcast_turn(session_id: str, turn: NegotiationTurn):
    if session_id in ws_connections:
        for ws in ws_connections[session_id]:
            try:
                await ws.send_text(turn.model_dump_json())
            except:
                pass

async def run_negotiation(session_id: str):
    session = negotiation_sessions[session_id]
    dual_env = DualAgentEnv(session)
    
    seller_runner = AgentRunner(NegotiationRole.seller, session.seller_config, openai_client, os.getenv("MODEL_NAME", "gpt-4o-mini"))
    client_runner = AgentRunner(NegotiationRole.client, session.client_config, openai_client, os.getenv("MODEL_NAME", "gpt-4o-mini"))
    
    while not dual_env.is_complete():
        # Seller turn
        obs_s = dual_env.get_observation(NegotiationRole.seller)
        action_s = await seller_runner.decide_action(obs_s)
        _, _, done = dual_env.step_seller(action_s)
        await broadcast_turn(session_id, session.negotiation_history[-1])
        await asyncio.sleep(2) # Fake typing delay
        if done: break
        
        # Client turn
        obs_c = dual_env.get_observation(NegotiationRole.client)
        action_c = await client_runner.decide_action(obs_c)
        _, _, done = dual_env.step_client(action_c)
        await broadcast_turn(session_id, session.negotiation_history[-1])
        await asyncio.sleep(2)
        if done: break
        
    session.status = "completed"
    await broadcast_turn(session_id, NegotiationTurn(
        turn_number=session.turn, speaker="system", action_type="skip", clause_id="", 
        content="Negotiation complete. Please review and sign the final agreement."
    ))

STATIC_DIR = os.path.join(os.path.dirname(__file__),"..","frontend","out")
if os.path.exists(STATIC_DIR):
    app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True))

@app.get("/")
def root(): 
    if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    return {"name":"ContractEnv","version":"1.0.0"}
