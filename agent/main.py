"""Main entry point for Idolly Agent Server"""
import uvicorn
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('idolly_agent_server.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the Idolly Agent Server"""
    logger.info("Starting Idolly Agent Server...")
    logger.info(f"Configuration: {settings.dict()}")
    
    # Run the FastAPI application
    uvicorn.run(
        "src.api.routes:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

if __name__ == "__main__":
    main()