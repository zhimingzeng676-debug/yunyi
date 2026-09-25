"""Process .pth files for this disposable --target dependency installation."""
import site
from pathlib import Path

site.addsitedir(str(Path(__file__).resolve().parents[2] / '.tools' / 'python'))
