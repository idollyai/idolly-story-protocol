"""Autonomous Idol Agent Implementation"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import json

from agent.agents.base_agent import BaseAgent
from agent.story_protocol.client import StoryProtocolClient
from agent.services.content_generator import ContentGenerator
from agent.services.style_mixer import StyleMixer
from agent.utils.ipfs_client import IPFSClient

logger = logging.getLogger(__name__)

class IdolAgent(BaseAgent):
    """Autonomous agent for managing AI Idols"""
    
    def __init__(
        self, 
        idol_id: str,
        idol_metadata: Dict[str, Any],
        story_client: StoryProtocolClient,
        content_generator: ContentGenerator,
        style_mixer: StyleMixer,
        ipfs_client: IPFSClient,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Idol Agent
        
        Args:
            idol_id: The IP ID of the idol
            idol_metadata: Metadata about the idol (personality, style, etc)
            story_client: Story Protocol client
            content_generator: AI content generation service
            style_mixer: Style mixing service
            ipfs_client: IPFS client for content storage
            config: Optional configuration
        """
        super().__init__(f"idol-{idol_id}", story_client, config)
        
        self.idol_id = idol_id
        self.idol_metadata = idol_metadata
        self.content_generator = content_generator
        self.style_mixer = style_mixer
        self.ipfs_client = ipfs_client
        
        # Agent-specific configuration
        self.content_strategy = config.get("content_strategy", {
            "posting_frequency": "2_hours",
            "content_types": ["image", "text", "remix"],
            "style_preferences": idol_metadata.get("style", {})
        })
        
        self.posting_schedule = self._generate_posting_schedule()
        self.licensed_ips = []  # Track IPs we've licensed
        self.created_derivatives = []  # Track our derivative works
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task"""
        task_type = task.get("type")
        
        try:
            if task_type == "generate_content":
                return await self._generate_content_task(task)
            elif task_type == "license_ip":
                return await self._license_ip_task(task)
            elif task_type == "create_remix":
                return await self._create_remix_task(task)
            elif task_type == "claim_royalties":
                return await self._claim_royalties_task(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Task execution failed for {self.agent_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "idol_id": self.idol_id,
            "is_active": self.is_active,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "content_created": len(self.created_derivatives),
            "licenses_held": len(self.licensed_ips),
            "next_post_time": self._get_next_post_time(),
            "metrics": await self.get_metrics()
        }
    
    async def generate_content(self, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Autonomously generate new content
        
        Args:
            content_type: Optional specific content type to generate
            
        Returns:
            Generated content information
        """
        logger.info(f"Generating content for idol {self.idol_id}")
        
        # Determine content type
        if not content_type:
            content_type = random.choice(self.content_strategy["content_types"])
        
        # Generate content based on idol's personality and style
        content_params = {
            "idol_name": self.idol_metadata.get("name"),
            "personality": self.idol_metadata.get("personality"),
            "style": self.idol_metadata.get("style"),
            "content_type": content_type
        }
        
        # Generate the content
        generated_content = await self.content_generator.create_content(content_params)
        
        # Upload to IPFS
        ipfs_hash = await self.ipfs_client.upload_json(generated_content["metadata"])
        
        # Prepare metadata for Story Protocol
        ip_metadata = {
            "metadata_uri": f"ipfs://{ipfs_hash}",
            "nft_metadata_uri": f"ipfs://{ipfs_hash}",
            "content_type": content_type,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Register as derivative IP of the idol
        derivative_ip = await self.story_client.create_derivative_content(
            parent_ip_id=self.idol_id,
            content_metadata={
                "child_ip_id": generated_content["ip_id"],
                "license_terms_ids": ["1"],  # Use default terms
                **ip_metadata
            }
        )
        
        # Track the created derivative
        self.created_derivatives.append({
            "ip_id": derivative_ip["ip_id"],
            "content_type": content_type,
            "created_at": datetime.utcnow(),
            "metadata": ip_metadata
        })
        
        logger.info(f"Content created: {derivative_ip['ip_id']}")
        return derivative_ip
    
    async def license_external_ip(self, target_ip_id: str) -> Dict[str, Any]:
        """
        License another IP for use in derivative works
        
        Args:
            target_ip_id: The IP to license
            
        Returns:
            License token information
        """
        logger.info(f"Licensing IP {target_ip_id} for idol {self.idol_id}")
        
        # Mint license token
        license_result = await self.story_client.mint_license_tokens(
            ip_id=target_ip_id,
            amount=1,
            receiver=self.idol_id  # Receive to idol's IP account
        )
        
        # Track licensed IP
        self.licensed_ips.append({
            "ip_id": target_ip_id,
            "license_tokens": license_result["license_token_ids"],
            "licensed_at": datetime.utcnow()
        })
        
        return license_result
    
    async def create_remix(self, style_ip_id: str) -> Dict[str, Any]:
        """
        Create a remix using a licensed style IP
        
        Args:
            style_ip_id: The style IP to apply
            
        Returns:
            Remix derivative information
        """
        logger.info(f"Creating remix for idol {self.idol_id} with style {style_ip_id}")
        
        # First, license the style IP if we haven't already
        existing_license = next(
            (lic for lic in self.licensed_ips if lic["ip_id"] == style_ip_id),
            None
        )
        
        if not existing_license:
            license_result = await self.license_external_ip(style_ip_id)
            license_token_id = license_result["license_token_ids"][0]
        else:
            license_token_id = existing_license["license_tokens"][0]
        
        # Apply style to create remix
        remix_content = await self.style_mixer.apply_style(
            base_ip_id=self.idol_id,
            style_ip_id=style_ip_id,
            parameters={
                "style_strength": 0.7,
                "preserve_identity": True
            }
        )
        
        # Upload remix metadata to IPFS
        ipfs_hash = await self.ipfs_client.upload_json(remix_content["metadata"])
        
        # Register as derivative with both parents
        derivative_result = await self.story_client.create_derivative_content(
            parent_ip_id=self.idol_id,
            content_metadata={
                "child_ip_id": remix_content["ip_id"],
                "metadata_uri": f"ipfs://{ipfs_hash}",
                "nft_metadata_uri": f"ipfs://{ipfs_hash}"
            },
            license_token_ids=[license_token_id]
        )
        
        # Track the remix
        self.created_derivatives.append({
            "ip_id": derivative_result["ip_id"],
            "content_type": "remix",
            "style_ip": style_ip_id,
            "created_at": datetime.utcnow()
        })
        
        return derivative_result
    
    async def analyze_market_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze market for licensing and collaboration opportunities"""
        opportunities = []
        
        # TODO: Implement market analysis logic
        # This would query trending IPs, analyze compatibility, etc.
        
        return opportunities
    
    async def claim_accumulated_royalties(self) -> Dict[str, Any]:
        """Claim any accumulated royalties"""
        if not self.created_derivatives:
            return {"status": "no_derivatives", "claimed": 0}
        
        child_ip_ids = [d["ip_id"] for d in self.created_derivatives]
        
        result = await self.story_client.claim_royalties(
            ip_id=self.idol_id,
            child_ip_ids=child_ip_ids
        )
        
        logger.info(f"Claimed royalties for idol {self.idol_id}: {result}")
        return result
    
    # Private helper methods
    
    def _generate_posting_schedule(self) -> List[datetime]:
        """Generate a posting schedule based on strategy"""
        schedule = []
        frequency = self.content_strategy.get("posting_frequency", "2_hours")
        
        # Parse frequency
        if frequency == "hourly":
            interval = timedelta(hours=1)
        elif frequency == "2_hours":
            interval = timedelta(hours=2)
        elif frequency == "daily":
            interval = timedelta(days=1)
        else:
            interval = timedelta(hours=2)  # Default
        
        # Generate schedule for next 24 hours
        current_time = datetime.utcnow()
        for i in range(24 // int(interval.total_seconds() / 3600)):
            schedule.append(current_time + (interval * i))
        
        return schedule
    
    def _get_next_post_time(self) -> Optional[str]:
        """Get the next scheduled post time"""
        current_time = datetime.utcnow()
        future_posts = [t for t in self.posting_schedule if t > current_time]
        
        if future_posts:
            return future_posts[0].isoformat()
        return None
    
    async def _generate_content_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content generation task"""
        content_type = task.get("content_type")
        result = await self.generate_content(content_type)
        return {"status": "success", "content": result}
    
    async def _license_ip_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute IP licensing task"""
        target_ip = task.get("target_ip_id")
        result = await self.license_external_ip(target_ip)
        return {"status": "success", "license": result}
    
    async def _create_remix_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remix creation task"""
        style_ip = task.get("style_ip_id")
        result = await self.create_remix(style_ip)
        return {"status": "success", "remix": result}
    
    async def _claim_royalties_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute royalty claiming task"""
        result = await self.claim_accumulated_royalties()
        return {"status": "success", "royalties": result}