#!/usr/bin/env python3
"""
md_to_json.py — Converte Monitoramento_Editais_Inovacao_YYYY-MM-DD.md em data/editais.json.

Uso:
    python scripts/md_to_json.py [caminho_para_md] [caminho_para_json]

Se nenhum argumento for passado, procura o .md mais recente no diretório raiz
e salva em data/editais.json.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def find_section(lines, title):
    """Encontra linhas a partir de um ## título (sem o ##)."""
    result = []
    in_section = False
    for line in lines:
        if line.startswith("## ") and title in line:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            result.append(line)
    return result


def parse_table(section_lines):
    """Parseia uma tabela markdown. Retorna (headers, rows).
    Ignora linhas introdutórias antes da tabela e para na primeira
    linha não-tabela após o início dos dados."""
    headers = None
    rows = []
    in_table = False
    for line in section_lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break  # fim da tabela
            continue  # pula linhas introdutórias
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if headers is None:
            headers = cells
            in_table = True
        else:
            row = {}
            for i, h in enumerate(headers):
                row[h] = cells[i] if i < len(cells) else ""
            rows.append(row)
    return headers, rows


def parse_novidades(section_lines):
    """Parseia a seção de novidades com suas subseções."""
    novidades = {
        "novos_editais": [],
        "editais_encerrados": [],
        "alteracoes_prazo": []
    }
    
    current_subsection = None
    headers = None
    rows = []
    
    for line in section_lines:
        stripped = line.strip()
        
        # Detecta subseções
        if stripped.startswith("### "):
            # Processa subseção anterior se existir
            if current_subsection and rows:
                if current_subsection == "novos_editais":
                    novidades["novos_editais"] = rows
                elif current_subsection == "editais_encerrados":
                    novidades["editais_encerrados"] = rows
                elif current_subsection == "alteracoes_prazo":
                    novidades["alteracoes_prazo"] = rows
                rows = []
                headers = None
            
            if "novos editais" in stripped.lower():
                current_subsection = "novos_editais"
            elif "encerrados" in stripped.lower():
                current_subsection = "editais_encerrados"
            elif "alterações" in stripped.lower() or "alteracoes" in stripped.lower():
                current_subsection = "alteracoes_prazo"
            continue
        
        # Parseia tabelas
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if headers is None:
                headers = cells
            else:
                row = {}
                for i, h in enumerate(headers):
                    row[h] = cells[i] if i < len(cells) else ""
                rows.append(row)
    
    # Processa última subseção
    if current_subsection and rows:
        if current_subsection == "novos_editais":
            novidades["novos_editais"] = rows
        elif current_subsection == "editais_encerrados":
            novidades["editais_encerrados"] = rows
        elif current_subsection == "alteracoes_prazo":
            novidades["alteracoes_prazo"] = rows
    
    return novidades


def parse_markdown(text: str) -> dict:
    """Parseia o markdown estruturado do monitor de editais."""
    data = {
        "meta": {},
        "stats": {},
        "novidades": {},
        "resumo_executivo": [],
        "alerta_prazo": "",
        "editais": [],
        "aderencia": [],
        "nao_confirmado": []
    }

    lines = text.split("\n")

    # --- Meta ---
    for line in lines[:10]:
        m = re.match(r"\*\*Data de referência:\*\*\s*(.+)", line)
        if m:
            raw = m.group(1).strip()
            data["meta"]["reference_date"] = raw.split("·")[0].strip().rstrip("—").strip()
            data["meta"]["reference_date_formatted"] = raw
        m = re.match(r"\*\*Escopo:\*\*\s*(.+)", line)
        if m:
            data["meta"]["scope"] = m.group(1).strip()
        m = re.match(r"\*\*Metodologia:\*\*\s*(.+)", line)
        if m:
            data["meta"]["methodology"] = m.group(1).strip()

    # --- Resumo Executivo ---
    resumo_lines = find_section(lines, "Resumo Executivo")
    for line in resumo_lines:
        m = re.match(r"[-•]\s*(.+)", line)
        if m:
            text = m.group(1).strip()
            # strip markdown bold/italic markers
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            data["resumo_executivo"].append(text)

    # --- Alerta de prazo (from markdown blockquote) ---
    for line in lines:
        m = re.match(r">\s*\*\*Alerta de prazo:\*\*\s*(.+)", line)
        if m:
            data["alerta_prazo"] = m.group(1).strip()
            break

    # --- Stats ---
    for line in data["resumo_executivo"]:
        clean = line.replace("**", "").replace("*", "")
        # abertos: "Abertos agora: 30 editais" or "30 editais abertos"
        m = re.search(r"(\d+)\s+editais?\s*(?:abertos|aberto)", clean, re.I) or re.search(r"(?:abertos|aberto)\D+(\d+)", clean, re.I)
        if m: data["stats"]["abertos"] = int(m.group(1))
        # continuos: "6 linhas de fluxo contínuo"
        m = re.search(r"(\d+)\s+linhas?\s+de\s+fluxo\s+cont.nu", clean, re.I)
        if m: data["stats"]["continuos"] = int(m.group(1))
        # em_breve: "Em breve: 3 chamadas internacionais"
        m = re.search(r"em\s+breve\D+(\d+)", clean, re.I)
        if m: data["stats"]["em_breve"] = int(m.group(1))
        # encerram: "11 editais fecham até"
        m = re.search(r"(\d+)\s+editais?\s+fecham", clean, re.I)
        if m: data["stats"]["encerram_7d"] = int(m.group(1))
        # nao_confirmado: "9 itens ... não confirmado"
        m = re.search(r"(\d+)\s+itens?", clean, re.I)
        if m: data["stats"]["nao_confirmado"] = int(m.group(1))

    # --- Novidades desde última atualização ---
    novidades_lines = find_section(lines, "Novidades desde")
    if novidades_lines:
        data["novidades"] = parse_novidades(novidades_lines)

    # --- Editais ---
    editais_lines = find_section(lines, "Tabela de Editais")
    _, editais_rows = parse_table(editais_lines)
    for row in editais_rows:
        edital_name = row.get("Edital", "").strip()
        # skip separator rows (e.g. "**Fluxo contínuo**" headers)
        if not edital_name or edital_name.startswith("**") and row.get("Fonte", "").strip() == "":
            continue
        status = "aberto"
        s = row.get("Status", "").lower()
        encerramento = row.get("Encerramento", "").strip().lower()
        dias = row.get("Dias restantes", "").strip()
        abertura = row.get("Abertura", "").strip().lower()
        # Priority: explicit status > inferred from dates
        if "breve" in s:
            status = "breve"
        elif "contínuo" in s or "continuo" in s:
            status = "continuo"
        elif encerramento in ("contínuo", "contínuo (banco de propostas)") or "permanente" in abertura:
            # no deadline AND not "em breve" → continuous
            status = "continuo"
        # Categorize tipo_publico
        publico_raw = row.get("Público-alvo", "").strip().lower()
        empresa_keywords = ["empresa", "empresas", "mpe", "média", "grande", "startup", "ict", "consórcio", "parceria", "pme", "industri", "tecnológica", "micro/pequena", "unidades"]
        pessoa_keywords = ["pessoa física", "pf", "professor", "estudante", "pesquisador", "mulher", "bolsa", "docente", "orientador", "escola", "universidade", "ict/universidade"]
        tipo = "Pessoa Física" if any(kw in publico_raw for kw in pessoa_keywords) else "Empresa"

        # Strip markdown bold from dias
        dias_raw = row.get("Dias restantes", "")
        dias_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', dias_raw).strip()

        data["editais"].append({
            "edital": edital_name,
            "fonte": row.get("Fonte", ""),
            "status": status,
            "abertura": row.get("Abertura", ""),
            "encerramento": row.get("Encerramento", ""),
            "dias": dias_clean,
            "tipo_publico": tipo,
            "publico": row.get("Público-alvo", ""),
            "valor": row.get("Valor/Faixa", ""),
            "contrapartida": row.get("Contrapartida", ""),
            "exigencias": row.get("Principais exigências", ""),
            "link": row.get("Link", ""),
            "grupo": "contínuo" if status == "continuo" else None
        })

    # --- Aderência ---
    aderencia_lines = find_section(lines, "Aderência com os institutos")
    _, aderencia_rows = parse_table(aderencia_lines)
    for row in aderencia_rows:
        grau = "media"
        g = row.get("Grau de aderência", "").lower()
        if "alta" in g:
            grau = "alta"
        elif "baixa" in g:
            grau = "baixa"
        elif "sem aderência" in g:
            grau = "none"
        data["aderencia"].append({
            "edital": row.get("Edital", ""),
            "institutos": row.get("Instituto(s) com maior aderência", ""),
            "grau": grau,
            "foco_educacional": row.get("Foco educacional?", ""),
            "justificativa": row.get("Justificativa", "")
        })

    # --- Não confirmado ---
    nao_conf_lines = find_section(lines, "Não confirmado")
    _, nao_conf_rows = parse_table(nao_conf_lines)
    for row in nao_conf_rows:
        data["nao_confirmado"].append({
            "edital": row.get("Edital", ""),
            "fonte": row.get("Fonte", ""),
            "motivo": row.get("Motivo", "")
        })

    return data


def find_latest_md():
    """Encontra o .md mais recente no diretório raiz."""
    md_files = list(ROOT.glob("Monitoramento_*.md"))
    if not md_files:
        return None
    return max(md_files, key=lambda p: p.stat().st_mtime)


def main():
    if len(sys.argv) > 1:
        md_path = Path(sys.argv[1])
    else:
        md_path = find_latest_md()
        if not md_path:
            print("Nenhum arquivo Monitoramento_*.md encontrado.")
            sys.exit(1)

    if len(sys.argv) > 2:
        json_path = Path(sys.argv[2])
    else:
        json_path = ROOT / "data" / "editais.json"

    print(f"Lendo: {md_path}")
    text = md_path.read_text(encoding="utf-8")
    data = parse_markdown(text)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo: {json_path}")

    # Also generate data/editais.js (embedded data for file:// compatibility)
    js_path = json_path.parent / "editais.js"
    js_content = "window.EDITAIS_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    js_path.write_text(js_content, encoding="utf-8")
    print(f"Salvo: {js_path}")

    print(f"  Editais: {len(data['editais'])}")
    print(f"  Aderência: {len(data['aderencia'])}")
    print(f"  Não confirmado: {len(data['nao_confirmado'])}")


if __name__ == "__main__":
    main()
