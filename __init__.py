"""
Koukoutu ComfyUI Nodes
Background removal and other AI processing nodes using Koukoutu API
"""

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Try to load the main background removal node
try:
    from .nodes.background_removal import KoukoutuBackgroundRemoval
    NODE_CLASS_MAPPINGS["KoukoutuBackgroundRemoval"] = KoukoutuBackgroundRemoval
    NODE_DISPLAY_NAME_MAPPINGS["KoukoutuBackgroundRemoval"] = "Koukoutu Background Removal"
    print("Koukoutu Background Removal node loaded successfully")
except Exception as e:
    print(f"Failed to load main background removal node: {e}")
    
    # Try to load the simplified version
    try:
        from .nodes.background_removal_simple import KoukoutuBackgroundRemovalSimple
        NODE_CLASS_MAPPINGS["KoukoutuBackgroundRemovalSimple"] = KoukoutuBackgroundRemovalSimple
        NODE_DISPLAY_NAME_MAPPINGS["KoukoutuBackgroundRemovalSimple"] = "Koukoutu Background Removal (Simple)"
        print("Koukoutu Background Removal (Simple) node loaded successfully")
    except Exception as e2:
        print(f"Failed to load simplified background removal node: {e2}")
        print("Please ensure all dependencies are installed:")
        print("pip install requests Pillow numpy torch")

if not NODE_CLASS_MAPPINGS:
    print("No Koukoutu nodes could be loaded. Please check your dependencies.")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
