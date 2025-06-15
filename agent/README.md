# Idolly Agent Server

## Project Overview
Idolly Agent Server is the core component of an autonomous IP economy platform leveraging Story Protocol. It handles autonomous content generation, IP licensing, and social media management for AI idols.

## Architecture Design

### Project Structure
```
idolly-agent-server/
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # Base agent class
│   │   ├── idol_agent.py          # Autonomous idol agent
│   │   ├── social_agent.py        # Social media management agent
│   │   └── licensing_agent.py     # IP licensing agent
│   ├── story_protocol/
│   │   ├── client.py              # Story Protocol client wrapper
│   │   ├── ip_asset.py            # IP Asset management
│   │   ├── licensing.py           # Licensing management
│   │   └── royalty.py             # Royalty management
│   ├── services/
│   │   ├── content_generator.py   # AI content generation
│   │   ├── style_mixer.py         # Style mixing service
│   │   ├── metadata_manager.py    # Metadata management
│   │   └── scheduler.py           # Background task scheduler
│   ├── api/
│   │   ├── routes.py              # REST API endpoints
│   │   └── websocket.py           # WebSocket connection management
│   └── utils/
│       ├── ipfs_client.py         # IPFS client
│       └── wallet_manager.py      # Wallet management
├── config/
│   └── settings.py                # Environment settings
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Core Components

### 1. Story Protocol Integration

#### Story Protocol Client Wrapper
```python
# story_protocol/client.py
from story_protocol_python_sdk import StoryClient
from web3 import Web3

class StoryProtocolClient:
    def __init__(self, private_key: str, chain_id: str = "aeneid"):
        self.client = StoryClient(
            account=private_key,
            transport=Web3.HTTPProvider(os.getenv("RPC_PROVIDER_URL")),
            chain_id=chain_id
        )
        
    async def register_idol_ip(self, metadata: dict) -> dict:
        """Register idol as IP Asset"""
        pass
        
    async def create_derivative_content(self, parent_ip: str, content_metadata: dict) -> dict:
        """Create and register derivative content"""
        pass
        
    async def mint_license_tokens(self, ip_id: str, amount: int) -> dict:
        """Mint license tokens"""
        pass
```

#### IP Asset Management
```python
# story_protocol/ip_asset.py
class IPAssetManager:
    async def register_idol_workflow(self, idol_data: dict):
        # 1. Upload metadata to IPFS
        ipfs_hash = await upload_to_ipfs(idol_data)
        
        # 2. Register IP Asset on Story Protocol
        ip_result = await story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=SPG_CONTRACT,
            ip_metadata={
                "ip_metadata_uri": f"ipfs://{ipfs_hash}",
                "ip_metadata_hash": calculate_hash(idol_data)
            }
        )
        
        # 3. Set license terms
        license_terms = await story_client.IPAsset.register_pil_terms(
            ip_id=ip_result["ip_id"],
            terms=create_default_license_terms()
        )
        
        return ip_result
```

### 2. Autonomous Agent System

#### Base Agent Class
```python
# agents/base_agent.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, agent_id: str, story_client: StoryProtocolClient):
        self.agent_id = agent_id
        self.story_client = story_client
        self.is_active = False
        
    @abstractmethod
    async def execute_task(self, task: dict):
        pass
        
    async def start(self):
        self.is_active = True
        
    async def stop(self):
        self.is_active = False
```

#### Idol Agent Implementation
```python
# agents/idol_agent.py
class IdolAgent(BaseAgent):
    def __init__(self, idol_id: str, story_client: StoryProtocolClient):
        super().__init__(idol_id, story_client)
        self.idol_id = idol_id
        self.content_strategy = {}
        self.posting_schedule = {}
        
    async def generate_content(self):
        """Autonomously generate content"""
        # AI content generation
        content = await self.content_generator.create_post()
        
        # Register as derivative IP on Story Protocol
        derivative_ip = await self.story_client.create_derivative_content(
            parent_ip=self.idol_id,
            content_metadata=content
        )
        
        return derivative_ip
        
    async def license_external_ip(self, target_ip_id: str):
        """License another IP"""
        license_token = await self.story_client.mint_license_tokens(
            ip_id=target_ip_id,
            amount=1
        )
        return license_token
        
    async def create_remix(self, style_ip_id: str):
        """Create remix using style IP"""
        # License the style IP
        license_token = await self.license_external_ip(style_ip_id)
        
        # Generate remix content
        remix_content = await self.style_mixer.apply_style(
            base_content=self.idol_id,
            style_ip=style_ip_id
        )
        
        # Register as derivative IP (with two parent IPs)
        derivative_ip = await self.story_client.register_derivative_with_license_tokens(
            child_ip_id=remix_content["ip_id"],
            license_token_ids=[license_token["token_id"]]
        )
        
        return derivative_ip
```

### 3. API Design

#### REST API Endpoints
```python
# api/routes.py
from fastapi import FastAPI, WebSocket, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Idolly Agent Server", version="1.0.0")

class IdolCreationRequest(BaseModel):
    name: str
    personality: str
    style: str
    backstory: str
    wallet_address: str

class ContentGenerationRequest(BaseModel):
    content_type: str  # "image", "text", "video"
    theme: str
    style_preferences: dict

@app.post("/idols/create")
async def create_idol(request: IdolCreationRequest, background_tasks: BackgroundTasks):
    """60-second idol creation API"""
    # 1. Generate idol with AI
    idol_data = await ai_generator.create_idol(request)
    
    # 2. Register IP Asset on Story Protocol
    ip_result = await ip_asset_manager.register_idol_workflow(idol_data)
    
    # 3. Initialize agent (background)
    background_tasks.add_task(initialize_idol_agent, ip_result["ip_id"])
    
    return {
        "idol_id": ip_result["ip_id"],
        "transaction_hash": ip_result["tx_hash"],
        "explorer_url": f"https://aeneid.explorer.story.foundation/ipa/{ip_result['ip_id']}"
    }

@app.post("/idols/{idol_id}/content/generate")
async def generate_content(idol_id: str, request: ContentGenerationRequest):
    """Automated content generation"""
    agent = get_idol_agent(idol_id)
    content = await agent.generate_content(request.dict())
    return content

@app.post("/idols/{idol_id}/style/apply")
async def apply_style(idol_id: str, style_ip_id: str):
    """Apply style and create derivative IP"""
    agent = get_idol_agent(idol_id)
    remix = await agent.create_remix(style_ip_id)
    return remix

@app.get("/idols/{idol_id}/analytics")
async def get_idol_analytics(idol_id: str):
    """Idol analytics data"""
    return await analytics_service.get_idol_stats(idol_id)

@app.websocket("/idols/{idol_id}/agent/status")
async def agent_status(websocket: WebSocket, idol_id: str):
    """Real-time agent status monitoring"""
    await websocket.accept()
    agent = get_idol_agent(idol_id)
    
    try:
        while True:
            status = await agent.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(5)
    except Exception as e:
        await websocket.close()
```

### 4. Background Task System

#### Celery Task Scheduler
```python
# services/scheduler.py
from celery import Celery
from datetime import timedelta

celery_app = Celery('idolly_agent')
celery_app.conf.beat_schedule = {
    'autonomous-content-generation': {
        'task': 'services.scheduler.autonomous_content_generation',
        'schedule': timedelta(hours=2),
    },
    'license-management': {
        'task': 'services.scheduler.license_management',
        'schedule': timedelta(hours=24),
    },
    'ip-trading-bot': {
        'task': 'services.scheduler.ip_trading_bot',
        'schedule': timedelta(minutes=30),
    },
}

@celery_app.task
def autonomous_content_generation(idol_id: str):
    """Periodic content generation"""
    agent = get_idol_agent(idol_id)
    content = await agent.generate_content()
    await social_agent.post_to_platforms(content)

@celery_app.task
def license_management(idol_id: str):
    """License management and royalty claiming"""
    agent = get_idol_agent(idol_id)
    await agent.claim_royalties()
    await agent.renew_licenses()

@celery_app.task
def ip_trading_bot(idol_id: str):
    """Autonomous IP trading bot"""
    agent = get_idol_agent(idol_id)
    trading_opportunities = await agent.analyze_ip_market()
    for opportunity in trading_opportunities:
        await agent.execute_trade(opportunity)
```

### 5. Integration Workflows

#### Autonomous Licensing Workflow
```python
async def autonomous_licensing_workflow(agent: IdolAgent, target_ip: str):
    # 1. Check target IP license terms
    license_info = await story_client.License.get_license_terms(target_ip)
    
    # 2. Analyze cost efficiency
    if not agent.is_profitable_license(license_info):
        return None
    
    # 3. Mint license tokens
    license_token = await story_client.License.mint_license_tokens(
        licensor_ip_id=target_ip,
        amount=1,
        receiver=agent.wallet_address
    )
    
    # 4. Generate derivative content
    derivative = await agent.create_derivative_content(
        parent_ips=[agent.idol_id, target_ip],
        license_tokens=[license_token["token_id"]]
    )
    
    # 5. Distribute to social media
    await social_agent.distribute_content(derivative)
    
    return derivative
```

#### Revenue Optimization Workflow
```python
async def revenue_optimization_workflow(agent: IdolAgent):
    # 1. Analyze current royalty status
    royalty_data = await story_client.Royalty.get_royalty_data(agent.idol_id)
    
    # 2. Calculate optimal license terms
    optimal_terms = await analytics_service.calculate_optimal_license_terms(
        ip_id=agent.idol_id,
        market_data=royalty_data
    )
    
    # 3. Update license terms
    if optimal_terms != agent.current_license_terms:
        await story_client.License.update_license_terms(
            ip_id=agent.idol_id,
            new_terms=optimal_terms
        )
        agent.current_license_terms = optimal_terms
    
    # 4. Claim royalties
    claimable_revenue = await story_client.Royalty.claim_all_revenue(
        ancestor_ip_id=agent.idol_id,
        claimer=agent.wallet_address
    )
    
    return claimable_revenue
```

## Configuration

### Environment Settings
```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Story Protocol Configuration
    RPC_PROVIDER_URL: str = "https://aeneid.storyrpc.io"
    CHAIN_ID: str = "aeneid"
    SPG_NFT_CONTRACT: str
    WALLET_PRIVATE_KEY: str
    
    # IPFS Configuration
    IPFS_API_URL: str = "/ip4/127.0.0.1/tcp/5001"
    PINATA_JWT: str
    PINATA_GATEWAY: str
    
    # AI Services
    OPENAI_API_KEY: str
    IMAGE_SERVER_URL: str
    BLOCKCHAIN_SERVER_URL: str
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/idolly"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS: int = 100
    CONTENT_GENERATION_INTERVAL: int = 7200  # 2 hours
    LICENSE_MANAGEMENT_INTERVAL: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"
```


## Notes
- Image server and blockchain server exist separately; Agent server communicates with them via API
- All IP-related operations on Story Protocol are performed on-chain
- "Invisible IP" principle applied for user experience (abstracting blockchain complexity)