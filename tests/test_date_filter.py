import datetime
import datetime

from agent import answer_local as al


class DummyModel:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, convert_to_numpy=True):
        import numpy as np
        if isinstance(texts, list):
            return np.array([[1.0, 0.0] for _ in texts])
        return np.array([1.0, 0.0])


def fake_retriever(collection, qvec, top_k=5):
    a_ts = datetime.datetime(2025, 1, 11).timestamp()
    b_ts = datetime.datetime(2023, 6, 1).timestamp()
    return {
        "ids": ["docA", "docB"],
        "metadatas": [
            {"file_path": "C:/fake/path/15_Letters_and_Emails/fileA.pdf", "modified_time": a_ts, "chunk_index": 0, "doc_id": "docA"},
            {"file_path": "C:/fake/path/other/fileB.pdf", "modified_time": b_ts, "chunk_index": 0, "doc_id": "docB"},
        ],
        "documents": ["Text from A", "Text from B"],
    }


def test_date_and_file_ext_filter():
    # patch the heavy model and retriever in the module
    al.SentenceTransformer = lambda name=None: DummyModel()
    al.get_retriever = lambda: fake_retriever

    out = al.answer_local(
        "Test question",
        collection="court-files",
        top_k=5,
        format_mode="compact",
        path_contains="15_Letters_and_Emails",
        date_from="2025-01-01",
        date_to="2025-12-31",
        file_ext=".pdf",
    )

    assert "fileA" in out or "fileA.pdf" in out
    assert "fileB" not in out and "fileB.pdf" not in out
