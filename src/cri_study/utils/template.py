from pathlib import Path

from fastapi.templating import Jinja2Templates


def get_templates() -> Jinja2Templates:
    """共通のテンプレートインスタンスを取得"""
    templates_dir = Path(__file__).parent.parent / "templates"
    return Jinja2Templates(directory=str(templates_dir))


templates = get_templates()
