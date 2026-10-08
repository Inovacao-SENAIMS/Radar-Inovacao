#!/usr/bin/env python3
"""validate_editais.py — checagens de sanidade da resposta da pesquisa automática."""
import re

VALID_STATUS = {"aberto", "breve", "continuo"}
VALID_GRAU = {"alta", "media", "baixa", "none"}
PLACEHOLDERS = re.compile(r"\b(TODO|TBD|PENDENTE|LOREM)\b", re.I)
HTTP = re.compile(r"^https?://", re.I)


class ValidationError(ValueError):
    pass


def _fail(msg):
    raise ValidationError(msg)


def validate(data, previous=None, min_editais=10):
    if not isinstance(data, dict):
        _fail("resposta não é um objeto JSON")
    editais = data.get("editais")
    if not isinstance(editais, list):
        _fail("campo 'editais' ausente ou não é lista")
    if len(editais) < min_editais:
        _fail(f"poucos editais ({len(editais)} < {min_editais})")
    if not any(e.get("status") in ("aberto", "breve") for e in editais):
        _fail("nenhum edital aberto/em breve")
    for i, e in enumerate(editais):
        where = f"editais[{i}]"
        if e.get("status") not in VALID_STATUS:
            _fail(f"{where}: status inválido ({e.get('status')!r})")
        if not e.get("edital"):
            _fail(f"{where}: edital vazio")
        if not HTTP.match(str(e.get("link", ""))):
            _fail(f"{where}: link inválido ({e.get('link')!r})")
        for field in ("edital", "fonte", "valor", "exigencias", "publico"):
            if PLACEHOLDERS.search(str(e.get(field, ""))):
                _fail(f"{where}.{field}: placeholder proibido")
    for i, a in enumerate(data.get("aderencia", []) or []):
        if a.get("grau") not in VALID_GRAU:
            _fail(f"aderencia[{i}]: grau inválido ({a.get('grau')!r})")
    if previous:
        prev_n = len(previous.get("editais", []) or [])
        if prev_n and len(editais) < 0.7 * prev_n:
            _fail(f"queda suspeita: {len(editais)} editais vs {prev_n} anteriores (>30%)")
    if not data.get("resumo_executivo"):
        _fail("resumo_executivo vazio")
