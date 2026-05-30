import json
from pathlib import Path

from fastapi.templating import Jinja2Templates

def _load_github_repo_url() -> str:
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["github_repo_url"]

def get_templates() -> Jinja2Templates:
    """共通のテンプレートインスタンスを取得"""
    templates_dir = Path(__file__).parent.parent / "templates"
    t = Jinja2Templates(directory=str(templates_dir))
    t.env.globals["github_repo_url"] = _load_github_repo_url()
    return t

templates = get_templates()
