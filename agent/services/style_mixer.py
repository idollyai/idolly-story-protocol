"""Style Mixing Service for creating remixes"""
import logging
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime
import uuid

from config.settings import settings

logger = logging.getLogger(__name__)

class StyleMixer:
    """Service for applying styles and creating remixes"""
    
    def __init__(self):
        self.image_server_url = settings.IMAGE_SERVER_URL
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def apply_style(
        self, 
        base_ip_id: str,
        style_ip_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply a style IP to a base IP to create a remix
        
        Args:
            base_ip_id: The base IP to apply style to
            style_ip_id: The style IP to apply
            parameters: Style mixing parameters
                - style_strength: How strongly to apply the style (0-1)
                - preserve_identity: Whether to preserve base identity
                
        Returns:
            Remix content with metadata
        """
        params = parameters or {}
        style_strength = params.get("style_strength", 0.7)
        preserve_identity = params.get("preserve_identity", True)
        
        try:
            # For PoC, simulate style transfer
            # In production, this would call actual style transfer model
            
            remix_id = str(uuid.uuid4())
            
            # Call image server for style transfer
            async with self.session.post(
                f"{self.image_server_url}/style-transfer",
                json={
                    "base_image": f"ipfs://{base_ip_id}",  # Simplified for PoC
                    "style_image": f"ipfs://{style_ip_id}",
                    "style_strength": style_strength,
                    "preserve_identity": preserve_identity
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                else:
                    # Fallback for PoC
                    result = {
                        "success": True,
                        "remix_url": f"https://example.com/remixes/{remix_id}.png"
                    }
            
            # Prepare remix metadata
            metadata = {
                "content_id": remix_id,
                "type": "remix",
                "base_ip": base_ip_id,
                "style_ip": style_ip_id,
                "remix_params": {
                    "style_strength": style_strength,
                    "preserve_identity": preserve_identity
                },
                "created_at": datetime.utcnow().isoformat(),
                "remix_url": result.get("remix_url")
            }
            
            return {
                "ip_id": remix_id,
                "metadata": metadata,
                "content_url": result.get("remix_url"),
                "parent_ips": [base_ip_id, style_ip_id]
            }
            
        except Exception as e:
            logger.error(f"Style mixing failed: {str(e)}")
            raise
    
    async def batch_apply_style(
        self,
        base_ip_ids: list[str],
        style_ip_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        Apply style to multiple base IPs
        
        Args:
            base_ip_ids: List of base IP IDs
            style_ip_id: Style IP to apply
            parameters: Style mixing parameters
            
        Returns:
            List of remix results
        """
        tasks = [
            self.apply_style(base_ip, style_ip_id, parameters)
            for base_ip in base_ip_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        successful_results = [
            r for r in results 
            if not isinstance(r, Exception)
        ]
        
        # Log errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to apply style to {base_ip_ids[i]}: {str(result)}")
        
        return successful_results
    
    async def analyze_style_compatibility(
        self,
        base_ip_id: str,
        style_ip_id: str
    ) -> Dict[str, Any]:
        """
        Analyze compatibility between base and style IPs
        
        Args:
            base_ip_id: Base IP ID
            style_ip_id: Style IP ID
            
        Returns:
            Compatibility analysis
        """
        # For PoC, return simulated analysis
        # In production, this would use ML models to analyze compatibility
        
        compatibility_score = 0.85  # Simulated score
        
        return {
            "base_ip": base_ip_id,
            "style_ip": style_ip_id,
            "compatibility_score": compatibility_score,
            "recommended_settings": {
                "style_strength": 0.7 if compatibility_score > 0.8 else 0.5,
                "preserve_identity": True
            },
            "analysis": {
                "color_harmony": 0.9,
                "style_coherence": 0.8,
                "semantic_alignment": 0.85
            }
        }
    
    async def get_trending_styles(self, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get trending style IPs for remixing
        
        Args:
            limit: Number of styles to return
            
        Returns:
            List of trending style IPs
        """
        # For PoC, return mock data
        # In production, this would query blockchain/indexer for trending styles
        
        trending_styles = []
        
        style_names = [
            "Cyberpunk Neon", "Pastel Dreams", "Retro Wave",
            "Studio Ghibli", "Comic Book", "Watercolor",
            "Pixel Art", "Art Nouveau", "Glitch Art", "Vaporwave"
        ]
        
        for i, style_name in enumerate(style_names[:limit]):
            trending_styles.append({
                "ip_id": f"0x{uuid.uuid4().hex[:40]}",
                "name": style_name,
                "popularity_score": 100 - (i * 5),
                "usage_count": 1000 - (i * 100),
                "creator": f"0x{uuid.uuid4().hex[:40]}",
                "license_fee": 0  # Free for PoC
            })
        
        return trending_styles