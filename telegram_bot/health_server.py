"""
Simple health check server for Railway deployment
"""
import asyncio
import logging
from aiohttp import web
import threading
import os

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, port=8000):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        
    def setup_routes(self):
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.root)
        
    async def health_check(self, request):
        return web.json_response({
            'status': 'healthy',
            'service': 'telegram-funding-bot',
            'timestamp': asyncio.get_event_loop().time()
        })
        
    async def root(self, request):
        return web.json_response({
            'service': 'Telegram Funding Rate Bot',
            'status': 'running',
            'version': '1.0.0'
        })
    
    async def start(self):
        """Start the health server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await site.start()
            logger.info(f"Health server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
    
    async def stop(self):
        """Stop the health server"""
        if self.runner:
            await self.runner.cleanup()

def start_health_server_sync(port=8000):
    """Start health server in a separate thread"""
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = HealthServer(port)
        loop.run_until_complete(server.start())
        loop.run_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info(f"Health server thread started on port {port}")
    return thread