"""API Routes for Idolly Agent Server"""
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from agent.story_protocol.client import StoryProtocolClient
from agent.agents.idol_agent import IdolAgent
from agent.services.content_generator import ContentGenerator
from agent.services.style_mixer import StyleMixer
from agent.utils.ipfs_client import IPFSClient
from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Idolly Agent Server",
    version="1.0.0",
    description="Autonomous IP Economy Platform on Story Protocol"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent registry
agent_registry: Dict[str, IdolAgent] = {}

# Pydantic models for requests/responses

class IdolCreationRequest(BaseModel):
    name: str
    personality: Dict[str, Any]
    style: Dict[str, Any]
    backstory: str
    wallet_address: Optional[str] = None

class IdolCreationResponse(BaseModel):
    idol_id: str
    transaction_hash: str
    explorer_url: str
    agent_id: str

class ContentGenerationRequest(BaseModel):
    content_type: str = "image"  # "image", "text", "video"
    theme: Optional[str] = None
    style_preferences: Optional[Dict[str, Any]] = None

class StyleApplicationRequest(BaseModel):
    style_ip_id: str
    style_strength: float = 0.7
    preserve_identity: bool = True

class AgentStatusResponse(BaseModel):
    agent_id: str
    idol_id: str
    is_active: bool
    last_activity: Optional[str]
    content_created: int
    licenses_held: int
    next_post_time: Optional[str]
    metrics: Dict[str, Any]

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Idolly Agent Server",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/idols/create", response_model=IdolCreationResponse)
async def create_idol(
    request: IdolCreationRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new AI Idol and register it on Story Protocol
    """
    try:
        # Initialize clients
        story_client = StoryProtocolClient()
        content_generator = ContentGenerator()
        ipfs_client = IPFSClient()
        
        # Generate initial idol content
        async with content_generator:
            initial_content = await content_generator.create_content({
                "idol_name": request.name,
                "personality": request.personality,
                "style": request.style,
                "content_type": "image"
            })
        
        # Upload metadata to IPFS
        async with ipfs_client:
            idol_metadata = {
                "name": request.name,
                "description": f"AI Idol: {request.name}",
                "personality": request.personality,
                "style": request.style,
                "backstory": request.backstory,
                "created_at": datetime.utcnow().isoformat(),
                "image": initial_content["content_url"]
            }
            
            metadata_hash = await ipfs_client.upload_json(idol_metadata)
            nft_metadata_hash = await ipfs_client.upload_json({
                "name": request.name,
                "description": f"Idolly AI Idol - {request.name}",
                "image": initial_content["content_url"]
            })
        
        # Register IP Asset on Story Protocol
        ip_result = await story_client.register_idol_ip({
            "name": request.name,
            "metadata_uri": f"ipfs://{metadata_hash}",
            "nft_metadata_uri": f"ipfs://{nft_metadata_hash}",
            **idol_metadata
        })
        
        # Initialize autonomous agent in background
        agent_id = f"idol-{ip_result['ip_id']}"
        background_tasks.add_task(
            initialize_idol_agent,
            ip_result["ip_id"],
            idol_metadata
        )
        
        return IdolCreationResponse(
            idol_id=ip_result["ip_id"],
            transaction_hash=ip_result["tx_hash"],
            explorer_url=f"https://aeneid.explorer.story.foundation/ipa/{ip_result['ip_id']}",
            agent_id=agent_id
        )
        
    except Exception as e:
        logger.error(f"Idol creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/idols/{idol_id}/content/generate")
async def generate_content(
    idol_id: str,
    request: ContentGenerationRequest
):
    """Generate new content for an idol"""
    agent = agent_registry.get(f"idol-{idol_id}")
    
    if not agent:
        raise HTTPException(status_code=404, detail="Idol agent not found")
    
    try:
        # Add content generation task to agent
        await agent.add_task({
            "type": "generate_content",
            "content_type": request.content_type,
            "theme": request.theme,
            "style_preferences": request.style_preferences
        })
        
        # Wait for task completion (with timeout)
        await asyncio.sleep(2)  # Allow some processing time
        
        return {
            "status": "content_generation_initiated",
            "idol_id": idol_id,
            "content_type": request.content_type
        }
        
    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/idols/{idol_id}/style/apply")
async def apply_style(
    idol_id: str,
    request: StyleApplicationRequest
):
    """Apply a style to create a remix"""
    agent = agent_registry.get(f"idol-{idol_id}")
    
    if not agent:
        raise HTTPException(status_code=404, detail="Idol agent not found")
    
    try:
        # Add remix task to agent
        await agent.add_task({
            "type": "create_remix",
            "style_ip_id": request.style_ip_id,
            "parameters": {
                "style_strength": request.style_strength,
                "preserve_identity": request.preserve_identity
            }
        })
        
        return {
            "status": "remix_creation_initiated",
            "idol_id": idol_id,
            "style_ip_id": request.style_ip_id
        }
        
    except Exception as e:
        logger.error(f"Style application failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/idols/{idol_id}/status", response_model=AgentStatusResponse)
async def get_idol_status(idol_id: str):
    """Get the status of an idol's autonomous agent"""
    agent = agent_registry.get(f"idol-{idol_id}")
    
    if not agent:
        raise HTTPException(status_code=404, detail="Idol agent not found")
    
    status = await agent.get_status()
    return AgentStatusResponse(**status)

@app.get("/idols/{idol_id}/analytics")
async def get_idol_analytics(idol_id: str):
    """Get analytics data for an idol"""
    agent = agent_registry.get(f"idol-{idol_id}")
    
    if not agent:
        raise HTTPException(status_code=404, detail="Idol agent not found")
    
    metrics = await agent.get_metrics()
    
    # Add additional analytics
    analytics = {
        "agent_metrics": metrics,
        "content_statistics": {
            "total_content": len(agent.created_derivatives),
            "content_by_type": _count_content_by_type(agent.created_derivatives),
            "last_content_created": _get_last_content_time(agent.created_derivatives)
        },
        "licensing_statistics": {
            "total_licenses_held": len(agent.licensed_ips),
            "active_licenses": _count_active_licenses(agent.licensed_ips)
        },
        "engagement_metrics": {
            # Placeholder for social media metrics
            "estimated_reach": 0,
            "engagement_rate": 0
        }
    }
    
    return analytics

@app.websocket("/idols/{idol_id}/agent/status")
async def agent_status_websocket(websocket: WebSocket, idol_id: str):
    """WebSocket endpoint for real-time agent status monitoring"""
    await websocket.accept()
    
    agent = agent_registry.get(f"idol-{idol_id}")
    if not agent:
        await websocket.close(code=4004, reason="Idol agent not found")
        return
    
    try:
        while True:
            # Send status update every 5 seconds
            status = await agent.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for idol {idol_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.get("/styles/trending")
async def get_trending_styles(limit: int = 10):
    """Get trending style IPs for remixing"""
    style_mixer = StyleMixer()
    
    async with style_mixer:
        trending = await style_mixer.get_trending_styles(limit)
    
    return {"styles": trending}

@app.post("/idols/{idol_id}/royalties/claim")
async def claim_royalties(idol_id: str):
    """Claim accumulated royalties for an idol"""
    agent = agent_registry.get(f"idol-{idol_id}")
    
    if not agent:
        raise HTTPException(status_code=404, detail="Idol agent not found")
    
    try:
        result = await agent.claim_accumulated_royalties()
        return {
            "status": "success",
            "idol_id": idol_id,
            "royalties_claimed": result
        }
    except Exception as e:
        logger.error(f"Royalty claim failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def initialize_idol_agent(idol_id: str, idol_metadata: Dict[str, Any]):
    """Initialize an autonomous agent for an idol"""
    try:
        # Create service instances
        story_client = StoryProtocolClient()
        content_generator = ContentGenerator()
        style_mixer = StyleMixer()
        ipfs_client = IPFSClient()
        
        # Create agent
        agent = IdolAgent(
            idol_id=idol_id,
            idol_metadata=idol_metadata,
            story_client=story_client,
            content_generator=content_generator,
            style_mixer=style_mixer,
            ipfs_client=ipfs_client,
            config={
                "content_strategy": {
                    "posting_frequency": "2_hours",
                    "content_types": ["image", "text", "remix"]
                }
            }
        )
        
        # Start agent
        await agent.start()
        
        # Register in global registry
        agent_registry[agent.agent_id] = agent
        
        logger.info(f"Agent initialized for idol {idol_id}")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")

def _count_content_by_type(derivatives: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count content by type"""
    counts = {}
    for deriv in derivatives:
        content_type = deriv.get("content_type", "unknown")
        counts[content_type] = counts.get(content_type, 0) + 1
    return counts

def _get_last_content_time(derivatives: List[Dict[str, Any]]) -> Optional[str]:
    """Get timestamp of last created content"""
    if not derivatives:
        return None
    
    latest = max(derivatives, key=lambda x: x.get("created_at", datetime.min))
    return latest.get("created_at").isoformat() if latest.get("created_at") else None

def _count_active_licenses(licenses: List[Dict[str, Any]]) -> int:
    """Count active licenses (placeholder implementation)"""
    # For PoC, all licenses are considered active
    return len(licenses)

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Idolly Agent Server starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down agents...")
    
    # Stop all agents
    for agent in agent_registry.values():
        await agent.stop()
    
    logger.info("Idolly Agent Server shut down complete")