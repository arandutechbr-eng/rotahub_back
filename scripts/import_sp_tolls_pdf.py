"""Importa praças de pedágio do PDF ARTESP SP 2025 para o banco.

Uso (na pasta backend, com venv ativo):
    python -m scripts.import_sp_tolls_pdf
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import httpx

from app.core.database import SessionLocal
from app.repositories.toll_plaza import TollPlazaRepository
from app.schemas.toll_plaza import TollPlazaCreate, TollPlazaUpdate
from app.services.toll_plaza import TollPlazaService

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT.parent / "53b3922a-a33b-40f6-9e4c-46a6771e681d.pdf"
RAW_TXT = ROOT / "app" / "data" / "sp_tolls_raw.txt"
OUT_JSON = ROOT / "app" / "data" / "toll_plazas.json"
USER_AGENT = "RotaHub/0.1 (contato@rotahub.app)"

PLACE_FIXES = {
    "STA CRUZ PALMEIRAS": "Santa Cruz das Palmeiras",
    "STA CRUZ DO RIO PARDO": "Santa Cruz do Rio Pardo",
    "ESP. SANTO DO PINHAL": "Espírito Santo do Pinhal",
    "S. J. DA BOA VISTA": "São João da Boa Vista",
    "PRESIDENTE BERNADES": "Presidente Bernardes",
    "CAMPO LIMPO": "Campo Limpo Paulista",
    "RIACHO GRANDE": "São Bernardo do Campo",
    "BATISTINI": "São Bernardo do Campo",
    "PIRATININGA": "São Bernardo do Campo",
    "ELDORADO": "Diadema",
    "MORRO DO ALTO (TATUÍ)": "Tatuí",
    "MORRO DO ALTO (ITAPETININGA)": "Itapetininga",
    "PAULÍNIA A": "Paulínia",
    "PAULÍNIA B": "Paulínia",
    "PAULINIA A": "Paulínia",
    "PAULINIA B": "Paulínia",
    "GRAMADÃO": "Itapeva",
    "QUADRA": "Quadra",
    "IARAS": "Iaras",
    "ITATINGA": "Itatinga",
    "AVAÍ": "Avaí",
    "PIRAJUÍ": "Pirajuí",
    "GUARAÇAÍ": "Guaraçaí",
    "CAÇAPAVA": "Caçapava",
}


def slugify(value: str, max_len: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return cleaned[:max_len] or "praca"


def money_to_float(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def extract_pdf_text() -> str:
    if RAW_TXT.exists() and RAW_TXT.stat().st_size > 0:
        return RAW_TXT.read_text(encoding="utf-8", errors="replace")

    from pypdf import PdfReader

    reader = PdfReader(str(PDF_PATH))
    parts: list[str] = []
    for index, page in enumerate(reader.pages):
        parts.append(f"\n\n===== PAGE {index + 1} =====\n{page.extract_text() or ''}")
    text = "".join(parts)
    RAW_TXT.write_text(text, encoding="utf-8", errors="replace")
    return text


def normalize_block(text: str) -> str:
    # Junta quebras de linha para capturar nomes multilinha.
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", " ", text)
    # Garante espaço antes do marco quilométrico (ex.: PARDO300+930 -> PARDO 300+930).
    text = re.sub(r"(?<![+\d\s])(\d{1,3}\+\d{3})", r" \1", text)
    text = re.sub(r"\s+", " ", text)
    return text


def clean_place(place: str) -> str:
    place = re.sub(r"\s+", " ", place).strip(" *")
    place = re.sub(r"^\*+\s*", "", place)
    cut = re.search(
        r"\b(LOTE|PRA[CÇ]AS DE PED[AÁ]GIO|LOCALIZA|PASSEIO|COMERCIAL|Concession[aá]ria|PED[AÁ]GIOS CONCEDIDOS|=====|PAGE|Rodovia|Via Anhanguera|Rodoanel)\b",
        place,
        flags=re.IGNORECASE,
    )
    if cut:
        place = place[: cut.start()]
    place = re.sub(r"R\$\s*\d.*$", "", place).strip(" -/,")
    return place[:80].strip()


def parse_main_tables(text: str) -> list[dict[str, Any]]:
    block = normalize_block(text)
    pattern = re.compile(
        r"(?P<road>(?:Via|Rodovia|Rodoanel)(?:(?!(?:Via|Rodovia|Rodoanel)\b).){0,100}?)\s+"
        r"(?P<code>SP-?\s*\d{2,3}|SPA-?\s*\d{2,3}/\d{2,3}|SPI\s*\d{2,3}/\d{2,3})\s+"
        r"(?P<place>.{2,80}?)\s+"
        r"(?P<km>\d{1,3}\+\d{3})\s+"
        r"R\$\s*(?P<passeio>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"R\$\s*(?P<eixo>\d{1,3}(?:\.\d{3})*,\d{2})",
        flags=re.IGNORECASE,
    )

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in pattern.finditer(block):
        road = re.sub(r"\s+", " ", match.group("road")).strip(" -")
        road = re.sub(
            r".*?(Via|Rodovia|Rodoanel)",
            r"\1",
            road,
            count=1,
            flags=re.IGNORECASE,
        )
        road = re.sub(r"\s*=====.*$", "", road).strip()
        code = re.sub(r"\s+", "", match.group("code").upper())
        if code.startswith("SP") and not code.startswith("SP-") and not code.startswith("SPA") and not code.startswith("SPI"):
            code = code.replace("SP", "SP-", 1)
        place = clean_place(match.group("place"))
        if len(place) < 2:
            continue
        km = match.group("km")
        tariff = money_to_float(match.group("eixo"))

        plaza_code = slugify(f"{code}-{place}-{km}")
        if plaza_code in seen:
            continue
        seen.add(plaza_code)

        items.append(
            {
                "code": plaza_code,
                "name": f"Praça {place}"[:160],
                "road": f"{road} ({code})"[:160],
                "concessionaire": "ARTESP/SP 2025",
                "place_query": place,
                "km": km,
                "tariff_per_axle": tariff,
                "is_active": True,
                "notes": f"PDF ARTESP 01/07/2025 · km {km} · comercial por eixo",
            }
        )
    return items


def parse_viapaulista_tables(text: str) -> list[dict[str, Any]]:
    """Páginas com tabela CAT: usa CAT-1 Manual como tarifa por eixo base."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"(SP\s*\d{2,3})\s*-\s*([^\n(]+?)\s*\(km\s*(\d{1,3}\+\d{3})\)[\s\S]{0,400}?"
        r"1\s+CAT-1\s+[\d.,]+\s+([\d.,]+)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        road_code = re.sub(r"\s+", "", match.group(1).upper())
        if not road_code.startswith("SP-"):
            road_code = road_code.replace("SP", "SP-", 1)
        place = re.sub(r"\s+", " ", match.group(2)).strip()
        km = match.group(3)
        tariff = money_to_float(match.group(4))
        plaza_code = slugify(f"{road_code}-{place}-{km}")
        if plaza_code in seen:
            continue
        seen.add(plaza_code)
        items.append(
            {
                "code": plaza_code,
                "name": f"Praça {place}",
                "road": f"ViaPaulista ({road_code})",
                "concessionaire": "ViaPaulista / ARTESP 2025",
                "place_query": place,
                "km": km,
                "tariff_per_axle": tariff,
                "is_active": True,
                "notes": f"PDF ARTESP L29 · km {km} · CAT-1 Manual",
            }
        )
    return items


def geocode_place(client: httpx.Client, place: str, cache: dict[str, tuple[float, float] | None]) -> tuple[float, float] | None:
    query_place = PLACE_FIXES.get(place.upper(), place)
    query_place = re.sub(r"\s*\([^)]*\)\s*", " ", query_place)
    query_place = re.sub(
        r"\b(P[oó]rtico|BLOQUEIO|PaP|Pra[cç]a\s*\d+|TRECHO\s+\w+|Pista\s+\w+|Al[aá]\s+[^,]*)\b",
        " ",
        query_place,
        flags=re.IGNORECASE,
    )
    query_place = re.sub(r"\s+", " ", query_place).strip(" -/," )
    if len(query_place) < 3 or len(query_place) > 80:
        return None

    key = query_place.casefold()
    if key in cache:
        return cache[key]

    for candidate in (f"{query_place}, São Paulo, Brasil", f"{query_place}, SP, Brasil"):
        try:
            response = client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": candidate, "format": "json", "limit": 1, "countrycodes": "br"},
            )
            time.sleep(1.1)
            if response.status_code >= 400:
                continue
            payload = response.json()
        except Exception:
            time.sleep(1.1)
            continue
        if payload:
            coords = (float(payload[0]["lat"]), float(payload[0]["lon"]))
            cache[key] = coords
            return coords
    cache[key] = None
    return None


def upsert_plazas(plazas: list[dict[str, Any]]) -> tuple[int, int, int]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada.")

    created = updated = skipped = 0
    with SessionLocal() as session:
        service = TollPlazaService(TollPlazaRepository(session))
        for item in plazas:
            existing = service.repository.get_by_code(item["code"])
            payload = {
                "code": item["code"],
                "name": item["name"][:160],
                "road": item["road"][:160],
                "concessionaire": item["concessionaire"][:120],
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "tariff_per_axle": item["tariff_per_axle"],
                "is_active": True,
                "notes": item.get("notes"),
            }
            if existing is None:
                service.create_plaza(TollPlazaCreate(**payload))
                created += 1
            else:
                service.update_plaza(existing.id, TollPlazaUpdate(**payload))
                updated += 1
        session.commit()
    return created, updated, skipped


def main() -> None:
    if not PDF_PATH.exists() and not RAW_TXT.exists():
        raise SystemExit(f"PDF não encontrado: {PDF_PATH}")

    print("Extraindo texto…")
    text = extract_pdf_text()
    plazas = parse_main_tables(text) + parse_viapaulista_tables(text)
    print(f"Praças parseadas: {len(plazas)}")

    cache: dict[str, tuple[float, float] | None] = {}
    ready: list[dict[str, Any]] = []
    failed: list[str] = []

    with httpx.Client(timeout=30.0, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}) as client:
        for index, plaza in enumerate(plazas, start=1):
            coords = geocode_place(client, plaza["place_query"], cache)
            if coords is None:
                failed.append(f"{plaza['code']} ({plaza['place_query']})")
                print(f"[{index}/{len(plazas)}] SEM GEO: {plaza['name']}")
                continue
            plaza["latitude"] = coords[0]
            plaza["longitude"] = coords[1]
            ready.append(plaza)
            print(
                f"[{index}/{len(plazas)}] {plaza['name']} · {plaza['road']} · "
                f"R$ {plaza['tariff_per_axle']:.2f} · {coords[0]:.4f},{coords[1]:.4f}"
            )

    seed_payload = [
        {
            "id": item["code"],
            "name": item["name"],
            "road": item["road"],
            "concessionaire": item["concessionaire"],
            "latitude": item["latitude"],
            "longitude": item["longitude"],
            "tariff_per_axle": item["tariff_per_axle"],
        }
        for item in ready
    ]
    OUT_JSON.write_text(json.dumps(seed_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON atualizado: {OUT_JSON} ({len(seed_payload)} praças)")

    print("Importando no banco…")
    created, updated, _ = upsert_plazas(ready)
    print(f"Concluído. criadas={created} atualizadas={updated} sem_geo={len(failed)}")
    if failed:
        print("Sem geocoding (não importadas):")
        for item in failed[:30]:
            print(" -", item)
        if len(failed) > 30:
            print(f" - … e mais {len(failed) - 30}")


if __name__ == "__main__":
    main()
