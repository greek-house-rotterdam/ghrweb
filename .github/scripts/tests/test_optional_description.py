"""The description may be missing or empty: the bot never invents one."""

import hashlib
from unittest.mock import patch

import pytest

import translate as translate_mod
from translate import compute_source_hash, parse_markdown, translate_file

GR_WITH = "---\ntitle: Γεια\ndescription: Περιγραφή\nlang: gr\n---\nΚείμενο"
GR_WITHOUT = "---\ntitle: Γεια\nlang: gr\n---\nΚείμενο"
GR_EMPTY = "---\ntitle: Γεια\ndescription: ''\nlang: gr\n---\nΚείμενο"
GR_NULL = "---\ntitle: Γεια\ndescription:\nlang: gr\n---\nΚείμενο"


def _fake_translation(api_key, source_lang, target_lang, payload, guidelines):
    return {k: f"[{target_lang}] {v}" if v else v for k, v in payload.items()}


def _setup(tmp_path, gr_text):
    base = tmp_path / "src" / "content" / "news"
    for lang in ("gr", "nl", "en"):
        (base / lang).mkdir(parents=True)
    gr = base / "gr" / "post.md"
    gr.write_text(gr_text, encoding="utf-8")
    return gr, base / "nl" / "post.md", base / "en" / "post.md"


def _run(gr):
    """Translate; return (payloads sent to the model, kept translations)."""
    calls = []

    def fake(api_key, s, t, payload, g):
        calls.append(dict(payload))
        return _fake_translation(api_key, s, t, payload, g)

    with patch.object(translate_mod, "translate_payload", side_effect=fake):
        kept = translate_file("k", gr, "")
    return calls, kept


def _hash_of(text):
    return compute_source_hash(*parse_markdown(text))


@pytest.mark.parametrize("gr_text", [GR_WITHOUT, GR_EMPTY, GR_NULL])
def test_no_description_in_gives_none_out(tmp_path, gr_text):
    gr, nl, en = _setup(tmp_path, gr_text)
    calls, _ = _run(gr)
    assert len(calls) == 2
    assert all("description" not in c for c in calls)  # nothing to translate
    for path in (nl, en):
        fm, body = parse_markdown(path.read_text(encoding="utf-8"))
        assert "description" not in fm
        assert fm["title"] == f"[{fm['lang']}] Γεια"
        assert body == f"[{fm['lang']}] Κείμενο"


@pytest.mark.parametrize("gr_text", [GR_EMPTY, GR_NULL])
def test_missing_and_empty_descriptions_hash_alike(gr_text):
    assert _hash_of(gr_text) == _hash_of(GR_WITHOUT)


def test_hash_with_a_description_is_unchanged():
    """Pinned format: files with a description must hash exactly as before."""
    fm = {"title": "Hello", "description": "World"}
    expected = hashlib.sha256(
        "description:World\ntitle:Hello\nbody:Body".encode("utf-8")
    ).hexdigest()[:12]
    assert compute_source_hash(fm, "Body") == expected


def test_description_is_translated_when_present(tmp_path):
    gr, nl, _ = _setup(tmp_path, GR_WITH)
    calls, _ = _run(gr)
    assert all(c["description"] == "Περιγραφή" for c in calls)
    fm, _ = parse_markdown(nl.read_text(encoding="utf-8"))
    assert fm["description"] == "[nl] Περιγραφή"


def test_removed_greek_description_is_removed_from_translations(tmp_path):
    gr, nl, en = _setup(tmp_path, GR_WITH)
    _run(gr)
    gr.write_text(GR_WITHOUT, encoding="utf-8")
    calls, _ = _run(gr)
    assert len(calls) == 2  # the hash changed, so both are translated again
    for path in (nl, en):
        fm, _ = parse_markdown(path.read_text(encoding="utf-8"))
        assert "description" not in fm
        assert fm["source_hash"] == _hash_of(GR_WITHOUT)


def test_removed_greek_description_is_removed_from_a_kept_translation(tmp_path):
    gr, nl, _ = _setup(tmp_path, GR_WITH)
    _run(gr)
    nl.write_text(
        nl.read_text(encoding="utf-8").replace("[nl] Κείμενο", "Mijn correctie"),
        encoding="utf-8",
    )
    gr.write_text(GR_WITHOUT, encoding="utf-8")
    calls, kept = _run(gr)
    assert len(calls) == 1  # only English is translated again
    assert [path for path, _label in kept] == [nl]
    fm, body = parse_markdown(nl.read_text(encoding="utf-8"))
    assert "description" not in fm
    assert body == "Mijn correctie"  # the hand fix stays
    assert fm["source_hash"] == _hash_of(GR_WITHOUT)


def test_added_greek_description_reaches_the_translations(tmp_path):
    gr, nl, _ = _setup(tmp_path, GR_WITHOUT)
    _run(gr)
    gr.write_text(GR_WITH, encoding="utf-8")
    _run(gr)
    fm, _ = parse_markdown(nl.read_text(encoding="utf-8"))
    assert fm["description"] == "[nl] Περιγραφή"


def test_translation_hash_covers_a_file_without_description(tmp_path):
    gr, nl, _ = _setup(tmp_path, GR_WITHOUT)
    _run(gr)
    fm, body = parse_markdown(nl.read_text(encoding="utf-8"))
    assert fm["translation_hash"] == compute_source_hash(fm, body)
    assert not translate_mod.is_hand_edited(fm, body)
