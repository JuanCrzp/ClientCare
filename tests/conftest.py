import sys
from pathlib import Path

# Asegura que el directorio raíz esté en sys.path (para importar 'src.*')
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
