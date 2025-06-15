"""Background Task Scheduler using Celery"""
import logging
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from typing import Dict, Any

from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'idolly_agent',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'autonomous-content-generation': {
            'task': 'src.services.scheduler.autonomous_content_generation',
            'schedule': timedelta(seconds=settings.CONTENT_GENERATION_INTERVAL),
            'args': ()
        },
        'license-management': {
            'task': 'src.services.scheduler.license_management',
            'schedule': timedelta(seconds=settings.LICENSE_MANAGEMENT_INTERVAL),
            'args': ()
        },
        'ip-trading-bot': {
            'task': 'src.services.scheduler.ip_trading_bot',
            'schedule': timedelta(minutes=30),
            'args': ()
        },
        'royalty-collection': {
            'task': 'src.services.scheduler.royalty_collection',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
            'args': ()
        }
    }
)

@celery_app.task
def autonomous_content_generation():
    """Periodic content generation for all active agents"""
    logger.info("Running autonomous content generation task")
    
    # Import here to avoid circular imports
    from agent.api.routes import agent_registry
    
    active_agents = [
        agent for agent in agent_registry.values() 
        if agent.is_active
    ]
    
    logger.info(f"Processing {len(active_agents)} active agents")
    
    for agent in active_agents:
        try:
            # Schedule content generation
            asyncio.create_task(
                agent.add_task({
                    "type": "generate_content",
                    "scheduled": True
                })
            )
        except Exception as e:
            logger.error(f"Content generation failed for agent {agent.agent_id}: {str(e)}")
    
    return {
        "status": "completed",
        "agents_processed": len(active_agents)
    }

@celery_app.task
def license_management():
    """Manage licenses and explore new licensing opportunities"""
    logger.info("Running license management task")
    
    from agent.api.routes import agent_registry
    
    results = []
    
    for agent in agent_registry.values():
        if not agent.is_active:
            continue
            
        try:
            # Analyze market opportunities
            opportunities = asyncio.run(agent.analyze_market_opportunities())
            
            # Process top opportunities
            for opportunity in opportunities[:3]:  # Top 3 opportunities
                if opportunity.get("score", 0) > 0.7:  # High confidence
                    asyncio.create_task(
                        agent.add_task({
                            "type": "license_ip",
                            "target_ip_id": opportunity["ip_id"],
                            "reason": opportunity["reason"]
                        })
                    )
                    
            results.append({
                "agent_id": agent.agent_id,
                "opportunities_found": len(opportunities),
                "licenses_initiated": min(3, len(opportunities))
            })
            
        except Exception as e:
            logger.error(f"License management failed for agent {agent.agent_id}: {str(e)}")
    
    return {
        "status": "completed",
        "results": results
    }

@celery_app.task
def ip_trading_bot():
    """Autonomous IP trading based on market conditions"""
    logger.info("Running IP trading bot task")
    
    # Placeholder for trading logic
    # In production, this would:
    # 1. Analyze trending IPs
    # 2. Evaluate remix potential
    # 3. Execute strategic trades
    
    return {
        "status": "completed",
        "trades_evaluated": 0,
        "trades_executed": 0
    }

@celery_app.task
def royalty_collection():
    """Collect accumulated royalties for all agents"""
    logger.info("Running royalty collection task")
    
    from agent.api.routes import agent_registry
    
    total_claimed = 0
    agents_processed = 0
    
    for agent in agent_registry.values():
        if not agent.is_active or not agent.created_derivatives:
            continue
            
        try:
            result = asyncio.run(agent.claim_accumulated_royalties())
            
            if result.get("status") != "no_derivatives":
                total_claimed += result.get("claimed", 0)
                agents_processed += 1
                
        except Exception as e:
            logger.error(f"Royalty collection failed for agent {agent.agent_id}: {str(e)}")
    
    logger.info(f"Collected royalties for {agents_processed} agents, total: {total_claimed}")
    
    return {
        "status": "completed",
        "agents_processed": agents_processed,
        "total_claimed": total_claimed
    }

@celery_app.task
def health_check():
    """Periodic health check of all services"""
    logger.info("Running health check")
    
    health_status = {
        "celery": "healthy",
        "agents": {},
        "services": {}
    }
    
    # Check agent health
    from agent.api.routes import agent_registry
    
    for agent_id, agent in agent_registry.items():
        health_status["agents"][agent_id] = {
            "is_active": agent.is_active,
            "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
            "tasks_in_queue": agent.tasks_queue.qsize()
        }
    
    return health_status

# Helper function for async execution in Celery
import asyncio

def run_async(coro):
    """Run async coroutine in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()