"""Fast tests: no model download.  The embedder is replaced by a bag-of-letters fake."""

import random

import numpy as np
import pytest

from kiswahili_embed import corpus, pairs
from kiswahili_embed.embedder import SemanticIndex
from kiswahili_embed.evaluate import retrieval
from kiswahili_embed.noun_classes import NounClassGuesser, PrefixBaseline


class FakeEmbedder:
    name = "fake"

    def encode(self, texts, role="query"):
        single = isinstance(texts, str)
        items = [texts] if single else list(texts)
        out = np.zeros((len(items), 26), dtype=np.float32)
        for r, t in enumerate(items):
            for ch in t.lower():
                if "a" <= ch <= "z":
                    out[r, ord(ch) - 97] += 1
            # first letters matter most, like a noun-class prefix
            for i, ch in enumerate(t.lower()[:2]):
                if "a" <= ch <= "z":
                    out[r, ord(ch) - 97] += 5 - 2 * i
        out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-9
        return out[0] if single else out


RAW = """DIBAJI
Hii ni tafsiri mpya.

MWANZO
1 aMwanzo Mungu aliumba mbingu na nchi.
2 Nayo nchi ilikuwa haina umbo tena ilikuwa tupu,b giza lilikuwa juu ya vilindi vya maji.
16:12 Ay 6:5; 11:12; 24:5; 39:5; Hos 8:9; Za
104:11; Yer 2:24
j
17
3 cMungu akasema, “Iwepo nuru,” nayo nuru ikawepo.
"""


def test_clean_bible_drops_references_and_numbers():
    text = corpus.clean_bible(RAW)
    assert "16:12" not in text and "Hos" not in text
    sents = corpus.sentences(text)
    assert "Mwanzo Mungu aliumba mbingu na nchi." in sents
    assert any(s.startswith("Nayo nchi ilikuwa haina umbo tena ilikuwa tupu,") for s in sents)
    assert not any(any(ch.isdigit() for ch in s) for s in sents)
    assert all(not s.endswith(("aliumb", "nch")) for s in sents)   # last letters kept


def test_split_is_blockwise_and_complete():
    items = [f"s{i}" for i in range(4000)]
    train, test = corpus.split(items)
    assert len(train) + len(test) == 4000 and set(train).isdisjoint(test)
    assert test[:200] == items[1800:2000]


def test_noise_changes_sentence():
    rng = random.Random(0)
    s = "Kitabu kimeanguka chini ya meza kubwa ya mwalimu"
    assert all(pairs.add_noise(s, rng) != s for _ in range(20))


def test_make_pairs_kinds_and_prefixes():
    sents = [f"neno la {i} " + " ".join(["maneno"] * 12) for i in range(50)]
    ps = pairs.make_pairs(sents, n_noise=5, n_crop=5, n_neighbour=5)
    assert sorted({p.kind for p in ps}) == ["crop", "neighbour", "noise"]
    a, b = pairs.as_columns(ps)
    assert all(x.startswith("query: ") for x in a)
    for p, pos in zip(ps, b):
        assert pos.startswith("query: " if p.kind == "noise" else "passage: ")


def test_semantic_index_search_and_roundtrip(tmp_path):
    idx = SemanticIndex(FakeEmbedder())
    idx.add(["kitabu", "mbuzi", "zzz"])
    assert idx.search("kitabu", k=1)[0][2] == "kitabu"
    idx.save(tmp_path)
    loaded = SemanticIndex.load(tmp_path, embedder=FakeEmbedder())
    assert loaded.texts == idx.texts
    np.testing.assert_allclose(loaded.vectors, idx.vectors)


def test_retrieval_excludes_self_match():
    pool = ["kitabu", "kitabu", "mbuzi"]
    r = retrieval(FakeEmbedder(), ["kitabu"], pool, [1], exclude=[0])
    assert r["r@1"] == 1.0
    r = retrieval(FakeEmbedder(), ["kitabu"], pool, [2])
    assert r["r@1"] == 0.0


def test_noun_class_guesser_and_baseline():
    items = [("kiti", "7/8"), ("kikombe", "7/8"), ("kisu", "7/8"),
             ("mti", "3/4"), ("mto", "3/4"), ("mlima", "3/4")]
    g = NounClassGuesser(FakeEmbedder(), items, k=3)
    cls, share = g.guess("kitanda")
    assert cls == "7/8" and 0 < share <= 1
    assert PrefixBaseline(items).predict("kioo") == "7/8"


@pytest.mark.skipif(not (corpus.DATA_DIR / "search_eval.jsonl").exists(), reason="no eval file")
def test_search_eval_file_is_well_formed():
    import json
    lines = (corpus.DATA_DIR / "search_eval.jsonl").read_text(encoding="utf-8").splitlines()
    items = [json.loads(l) for l in lines if l.strip()]
    assert len(items) == 40 and all(it["query"] and it["passage"] for it in items)


def test_document_cleaning_repairs_ligatures_and_drops_forms():
    from kiswahili_embed.documents import clean_paragraphs, doc_sentences
    raw = ("Jina la Mtoto ____________ Umri (miezi)____\n\n"
           "Mtoto ana uoni haĮfu au haoni kabisa kwa muda mrefu.\n\n"
           "Kunywa maji saﬁ kila siku. D Osha mikono kwa sabuni kabla ya kula chakula.\n\n"
           "machozi yĂŶĂƟrirka kwenye jicho\n\n"
           "Ndiyo ☐ Hapana ☐\n\n"
           "Pika nyama mpaka iive kabisa ili kuepuka maambukizi. 44\n")
    paras = clean_paragraphs(raw)
    assert "Mtoto ana uoni hafifu au haoni kabisa kwa muda mrefu." in paras
    assert "Kunywa maji safi kila siku." in paras
    assert "Osha mikono kwa sabuni kabla ya kula chakula." in paras
    assert "Pika nyama mpaka iive kabisa ili kuepuka maambukizi." in paras
    assert not any("Ă" in p or "☐" in p or "___" in p for p in paras)
    assert doc_sentences(["Kula vizuri kila siku. Lala mapema kila usiku sana."]) == [
        "Kula vizuri kila siku.", "Lala mapema kila usiku sana."]


def test_split_documents_holds_out_groups():
    from kiswahili_embed.documents import Document, split_documents
    docs = [Document("a-IYCF", []), Document("Matibabu_x", []), Document("Mwongozo", [])]
    train, test = split_documents(docs)
    assert [d.name for d in train] == ["Mwongozo"] and len(test) == 2


def test_retrieval_accepts_gold_sets():
    pool = ["mbuzi", "kitabu", "kitabu kizuri"]
    r = retrieval(FakeEmbedder(), ["kitabu"], pool, [[1, 2]])
    assert r["r@1"] == 1.0


def test_doc_pairs_include_sections():
    from kiswahili_embed.documents import Document
    doc = Document("d", ["Kula chakula bora kila siku ya wiki. Kunywa maji safi ya kutosha kila siku."])
    kinds = {p.kind for p in pairs.make_doc_pairs([doc], n_noise=1)}
    assert {"section", "neighbour", "noise"} <= kinds


def test_health_eval_file_is_well_formed():
    import json
    path = corpus.DATA_DIR / "health_search_eval.jsonl"
    items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(items) == 150
    assert len({it["id"] for it in items}) == 150 and len({it["query"] for it in items}) == 150
    assert {it["who"] for it in items} == {"caregiver", "clinician"}
    assert all(it["gold"] and all(g.strip() for g in it["gold"]) for it in items)


def test_generated_questions_validate_and_score(tmp_path):
    import json
    from kiswahili_embed.documents import Document
    from kiswahili_embed.evaluate import generated_task
    from kiswahili_embed.generate_questions import plan, validate
    docs = [Document("IYCF-x", ["Mtoto apewe maziwa ya mama pekee kwa miezi sita ya mwanzo.",
                                "Kichwa"]),
            Document("Mwongozo", ["Kula mboga za majani na matunda kila siku kwa afya bora."])]
    jobs = plan(docs, target=4)
    assert [j["split"] for j in jobs] == ["test", "train"]      # 'Kichwa' is too short
    job = jobs[0]
    rows = validate(job, [
        {"question": "Mtoto anyonye kwa muda gani?", "who": "caregiver",
         "answer_quote": "maziwa ya mama pekee kwa miezi sita"},
        {"question": "Swali la uongo kabisa", "who": "caregiver", "answer_quote": "haipo kabisa"},
        {"question": "Mtoto anyonye kwa muda gani?", "who": "caregiver",
         "answer_quote": "maziwa ya mama pekee"}])
    assert len(rows) == 1 and rows[0]["split"] == "test"      # bad quote and duplicate dropped
    path = tmp_path / "q.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    q, pool, gold, role = generated_task(path, docs[0].paragraphs)
    assert q == ["Mtoto anyonye kwa muda gani?"] and gold == [[0]] and role == "passage"
