#!/usr/bin/env python3
"""web_search.py — provedor de busca web para a pesquisa automática (Groq).

O Groq não faz busca web nativa. Este módulo supre a "peça de busca": roda as
consultas e devolve trechos (título/url/trecho) que são injetados no prompt do
LLM antes da síntese em JSON.

Provedores suportados (chaves via variável de ambiente):
    TAVILY_API_KEY  → Tavily Search API (POST https://api.tavily.com/search)
    BRAVE_API_KEY   → Brave Search API (GET https://api.search.brave.com/res/v1/web/search)

Use ``resolve_provider`` / ``from_env`` para escolher automaticamente o provedor
conforme a chave disponível.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

TAVILY_URL = "https://api.tavily.com/search"
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
USER_AGENT = "curl/8.7.1"
PROVIDERS = ("tavily", "brave")


class SearchError(RuntimeError):
    pass


def _get(url, headers, timeout):
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SearchError(f"HTTP {exc.code}: {detail[:200]}") from exc
    except urllib.error.URLError as exc:
        raise SearchError(f"falha de rede na busca: {exc}") from exc


def _post(url, body, headers, timeout):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SearchError(f"HTTP {exc.code}: {detail[:200]}") from exc
    except urllib.error.URLError as exc:
        raise SearchError(f"falha de rede na busca: {exc}") from exc


def env_key(provider):
    return {
        "tavily": os.environ.get("TAVILY_API_KEY", ""),
        "brave": os.environ.get("BRAVE_API_KEY", ""),
    }.get(provider, "")


def resolve_provider(provider="auto", api_key=""):
    """Devolve (provider, api_key). Com 'auto', escolhe pelo que estiver no ambiente."""
    if provider in (None, "", "auto"):
        for candidate in PROVIDERS:
            if env_key(candidate):
                return candidate, env_key(candidate)
        raise SearchError("nenhuma chave de busca encontrada "
                          "(defina TAVILY_API_KEY ou BRAVE_API_KEY)")
    if provider not in PROVIDERS:
        raise SearchError(f"provedor de busca desconhecido: {provider!r} (use {'/'.join(PROVIDERS)})")
    key = api_key or env_key(provider)
    if not key:
        raise SearchError(f"chave de busca ausente para {provider} "
                          f"(defina {provider.upper()}_API_KEY)")
    return provider, key


def from_env(provider="auto", api_key=""):
    return resolve_provider(provider, api_key)


def _parse_tavily(payload):
    out = []
    for item in payload.get("results", []) or []:
        out.append({
            "title": str(item.get("title", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "snippet": str(item.get("content", "")).strip(),
        })
    return out


def _parse_brave(payload):
    out = []
    for item in (payload.get("web", {}) or {}).get("results", []) or []:
        out.append({
            "title": str(item.get("title", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "snippet": str(item.get("description", "")).strip(),
        })
    return out


def search(query, *, provider, api_key, count=5, timeout=30):
    """Executa uma consulta e devolve [{'title','url','snippet'}, ...]."""
    if provider == "tavily":
        payload = _post(TAVILY_URL, {
            "api_key": api_key, "query": query, "max_results": int(count),
            "search_depth": "basic", "include_answer": False,
        }, {"Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": USER_AGENT}, timeout)
        return _parse_tavily(payload)
    if provider == "brave":
        url = BRAVE_URL + "?" + urllib.parse.urlencode({"q": query, "count": int(count)})
        payload = _get(url, {"Accept": "application/json",
                             "X-Subscription-Token": api_key,
                             "User-Agent": USER_AGENT}, timeout)
        return _parse_brave(payload)
    raise SearchError(f"provedor de busca desconhecido: {provider!r}")


def build_context(queries, *, provider, api_key, count=5, timeout=30, max_chars=500):
    """Roda as consultas e monta um bloco de contexto em Markdown para o prompt."""
    blocks = []
    for query in queries:
        try:
            results = search(query, provider=provider, api_key=api_key, count=count, timeout=timeout)
        except SearchError as exc:  # falha isolada não derruba a rodada inteira
            blocks.append(f"### Consulta: {query}\n(falha na busca: {exc})")
            continue
        lines = [f"### Consulta: {query}"]
        if not results:
            lines.append("(sem resultados)")
        for r in results:
            snippet = str(r["snippet"])[:max_chars]
            lines.append(f"- {r['title']} — {r['url']}\n  {snippet}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def default_queries(year):
    """Consultas amplas seguindo o Passo 1 do PROMPT.md (escopo amplo)."""
    return [
        f"editais de inovação abertos {year} FINEP chamadas públicas",
        f"CNPq CAPES chamadas públicas abertas {year} inovação",
        f"FAPESP chamadas de propostas abertas {year} PIPE",
        f"CONFAP chamadas transnacionais Horizon Europe {year} Brasil",
        f"FAPERJ FAPESC FACEPE FUNDECT editais abertos {year} inovação",
        f"editais internacionais inovação {year} Eureka Eurostars BID MSCA",
        "Programa Centelha InovAtiva Brasil editais abertos",
    ]


def chunk_groups(year):
    """Grupos (rótulo, consultas) para a geração em blocos (limite de TPM do Groq)."""
    return [
        ("FINEP — chamadas gerais e Mais Inovação Brasil", [
            f"editais FINEP abertos {year} chamadas públicas inovação",
            f"FINEP Mais Inovação Brasil {year} prazo submissão temas",
        ]),
        ("FINEP/MCTI — subvenção, BNDES, EMBRAPII e cooperativas", [
            f"chamada FINEP MCTI {year} subvenção econômica empresas prazo",
            f"BNDES Mais Inovação EMBRAPII chamada {year}",
            f"FINEP cooperativas agricultura familiar {year} edital",
        ]),
        ("CNPq — bolsas e chamadas de inovação", [
            f"CNPq chamadas públicas abertas {year} inovação bolsas",
            f"chamada CNPq {year} RHAE MAI-DAI prazo submissão",
        ]),
        ("CAPES e outras agências federais", [
            f"CAPES edital {year} inovação bolsas aberto",
            f"edital federal inovação {year} MCTI aberto submissão",
        ]),
        ("FAPESP — PIPE, SPRINT, PRONEX e demais", [
            f"FAPESP chamadas abertas {year} PIPE",
            f"FAPESP SPRINT PRONEX M-ERA.NET {year} prazo",
        ]),
        ("FAPESP e parcerias internacionais da CONFAP", [
            f"FAPESP CONFAP chamada internacional {year} Horizon Europe",
            f"CONFAP Biodiversa Water4All FOREST chamada {year}",
        ]),
        ("FAPs estaduais — RJ, SC e PE", [
            f"FAPERJ editais abertos {year} inovação",
            f"FAPESC FACEPE chamadas abertas {year} inovação",
        ]),
        ("Centro-Oeste e Mato Grosso do Sul", [
            f"FUNDECT MS edital aberto {year} inovação",
            f"FUNDECT chamada pública {year} submissão",
            f"FAPEMAT FAPDF FAPEG editais abertos {year}",
        ]),
        ("Internacionais e empreendedorismo", [
            f"Eureka Eurostars MSCA chamada {year} prazo",
            f"BID Lab convocatória {year} capital empreendedor",
            f"Programa Centelha InovAtiva Brasil {year} inscrições",
        ]),
    ]
