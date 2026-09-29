from app.main import app

# Backward-compatible compatibility shim for the original v0.2 entrypoint.
# The canonical app is now located in backend/app/main.py but the old route
# contract remains unchanged for existing local clients and tooling.

