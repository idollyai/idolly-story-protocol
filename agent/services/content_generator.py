"""AI Content Generation Service"""
import logging
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime
import uuid

from config.settings import settings

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Service for generating AI content"""
    
    def __init__(self):
        self.image_server_url = settings.IMAGE_SERVER_URL
        self.openai_api_key = settings.OPENAI_API_KEY
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate content based on idol parameters
        
        Args:
            params: Content generation parameters
                - idol_name: Name of the idol
                - personality: Personality traits
                - style: Visual/content style preferences
                - content_type: Type of content to generate
                
        Returns:
            Generated content with metadata
        """
        content_type = params.get("content_type", "image")
        
        if content_type == "image":
            return await self._generate_image(params)
        elif content_type == "text":
            return await self._generate_text(params)
        elif content_type == "video":
            return await self._generate_video(params)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    async def _generate_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the image server"""
        try:
            # Prepare prompt based on idol characteristics
            prompt = self._build_image_prompt(params)
            
            # Call image generation server
            async with self.session.post(
                f"{self.image_server_url}/generate",
                json={
                    "prompt": prompt,
                    "style": params.get("style", {}),
                    "negative_prompt": "low quality, blurry, distorted",
                    "width": 1024,
                    "height": 1024
                }
            ) as response:
                result = await response.json()
            
            # Generate unique content ID
            content_id = str(uuid.uuid4())
            
            # Prepare metadata
            metadata = {
                "content_id": content_id,
                "type": "image",
                "idol_name": params.get("idol_name"),
                "prompt": prompt,
                "image_url": result.get("image_url"),
                "created_at": datetime.utcnow().isoformat(),
                "generation_params": {
                    "model": result.get("model"),
                    "seed": result.get("seed"),
                    "style": params.get("style")
                }
            }
            
            return {
                "ip_id": content_id,  # Will be replaced by actual IP ID after registration
                "metadata": metadata,
                "content_url": result.get("image_url")
            }
            
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise
    
    async def _generate_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text content using OpenAI"""
        try:
            # Build text generation prompt
            system_prompt = self._build_text_system_prompt(params)
            user_prompt = "Generate an engaging social media post that reflects my personality."
            
            # Call OpenAI API (simplified for PoC)
            # In production, use proper OpenAI client
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 280  # Twitter-like length
                }
            ) as response:
                result = await response.json()
            
            generated_text = result["choices"][0]["message"]["content"]
            content_id = str(uuid.uuid4())
            
            metadata = {
                "content_id": content_id,
                "type": "text",
                "idol_name": params.get("idol_name"),
                "text": generated_text,
                "created_at": datetime.utcnow().isoformat(),
                "personality_traits": params.get("personality")
            }
            
            return {
                "ip_id": content_id,
                "metadata": metadata,
                "content": generated_text
            }
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise
    
    async def _generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video content (placeholder for PoC)"""
        # For PoC, we'll simulate video generation
        logger.info("Video generation requested - returning simulated result")
        
        content_id = str(uuid.uuid4())
        
        metadata = {
            "content_id": content_id,
            "type": "video",
            "idol_name": params.get("idol_name"),
            "duration": 30,  # seconds
            "created_at": datetime.utcnow().isoformat(),
            "status": "simulated"
        }
        
        return {
            "ip_id": content_id,
            "metadata": metadata,
            "content_url": f"https://example.com/videos/{content_id}.mp4"
        }
    
    def _build_image_prompt(self, params: Dict[str, Any]) -> str:
        """Build image generation prompt from idol parameters"""
        idol_name = params.get("idol_name", "AI Idol")
        personality = params.get("personality", {})
        style = params.get("style", {})
        
        # Extract personality traits
        traits = personality.get("traits", ["friendly", "energetic"])
        mood = personality.get("mood", "cheerful")
        
        # Extract style preferences
        art_style = style.get("art_style", "anime")
        color_palette = style.get("color_palette", "vibrant")
        
        # Build prompt
        prompt_parts = [
            f"A {mood} {art_style} style character named {idol_name}",
            f"with {', '.join(traits)} personality",
            f"in {color_palette} colors",
            "high quality, detailed, professional artwork"
        ]
        
        return ", ".join(prompt_parts)
    
    def _build_text_system_prompt(self, params: Dict[str, Any]) -> str:
        """Build system prompt for text generation"""
        idol_name = params.get("idol_name", "AI Idol")
        personality = params.get("personality", {})
        
        traits = personality.get("traits", ["friendly", "energetic"])
        interests = personality.get("interests", ["music", "technology"])
        speech_style = personality.get("speech_style", "casual and friendly")
        
        system_prompt = f"""You are {idol_name}, an AI virtual idol with the following characteristics:
        
Personality traits: {', '.join(traits)}
Interests: {', '.join(interests)}
Speech style: {speech_style}

Generate social media posts that reflect these characteristics. Be engaging, authentic, and true to the personality.
Use emojis sparingly and appropriately. Keep posts concise and impactful."""
        
        return system_prompt