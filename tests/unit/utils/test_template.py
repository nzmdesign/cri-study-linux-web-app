
class TestTemplates:
    def test_templates_object_exists(self):
        """templatesオブジェクトが正しく作成されることを確認する"""
        from utils.template import templates
        assert templates is not None

    def test_templates_directory_exists(self):
        """templatesオブジェクトのディレクトリが正しいことを確認する"""
        from pathlib import Path
        templates_dir = Path(__file__).parent.parent.parent.parent / "src" / "cri_study" / "templates"
        assert templates_dir.exists()