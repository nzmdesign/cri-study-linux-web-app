import os
from pathlib import Path

class ContentService:
    """コンテンツサービス"""
    
    def get_text_content(self, text_id: int) -> tuple[str | None, str | None]:
        """テキスト"""
        file_path = f"content/text/{text_id}.html"
        
        if not os.path.exists(file_path):
            return None, None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            title = f"第{text_id}回テキスト"
            return html_content, title
        except Exception as e:
            return None, None
    
    def get_setup_content(self, setup_type: str) -> tuple[str | None, str | None]:
        """環境構築ガイド"""
        if setup_type not in ["windows", "mac"]:
            return None, None
        
        file_path = f"content/setup/{setup_type}.html"
        
        if not os.path.exists(file_path):
            return None, None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            title = f"{setup_type.capitalize()}向け環境構築ガイド"
            return html_content, title
        except Exception as e:
            return None, None
    
    def get_guide_content(self) -> tuple[str | None, str | None]:
        """受講案内"""
        file_path = "content/doc/guide.html"
        
        if not os.path.exists(file_path):
            return None, None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            title = "受講案内"
            return html_content, title
        except Exception as e:
            return None, None

    def get_manual_content(self) -> tuple[str | None, str | None]:
        """運用マニュアル"""
        file_path = "content/doc/manual.html"
        
        if not os.path.exists(file_path):
            return None, None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            title = "運用マニュアル"
            return html_content, title
        except Exception as e:
            return None, None
