# src/utils.py
import os

def load_stylesheet() -> str:
    """
    Load the QSS stylesheet from file.
    Uses relative path based on this file's location.
    """
    # Get directory of this file (utils.py)
    current_dir = os.path.dirname(__file__)
    qss_path = os.path.join(current_dir, "styles.qss")

    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {qss_path} not found. Using fallback style.")
        return """
        QMainWindow { background-color: #f0f0f0; }
        QLabel { color: #333; }
        """
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""