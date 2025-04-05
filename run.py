 #!/usr/bin/env python
"""
Run script for the KitchenSage application.
"""
import uvicorn
from typing import Optional

def run_app(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """
    Run the FastAPI application with uvicorn.
    
    Args:
        host: Host IP address to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
    """
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    run_app()