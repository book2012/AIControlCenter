from core.knowledge.loader import MarkdownLoader


def test_loader_readme():
    loader = MarkdownLoader()

    data = loader.load("README.md")

    assert data["name"] == "README.md"
    assert len(data["content"]) > 0
    assert data["lines"] > 0
