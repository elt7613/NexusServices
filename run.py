import os
import sys
import uvicorn
from dotenv import load_dotenv
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

APP_MODULE = "app:app"

def main():
    """Run the server."""
    # Load environment variables
    load_dotenv()
    # Run the server with standard asyncio loop instead of uvloop to avoid conflicts
    uvicorn.run(
        APP_MODULE,
        host="0.0.0.0",
        port=8021,
        reload=True,
        loop="asyncio"  # Use standard asyncio instead of uvloop
    )

if __name__ == "__main__":
    main() 