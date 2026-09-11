"""Backend opcional do SPA.

O dashboard funciona sem esta API, lendo os JSON estaticos de web/public/dados.
Subir a API habilita o botao de atualizar os dados direto pela interface.
"""

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import exportar_web
from main import coletar_fundamentus, filtrar_negociaveis, salvar_csv

app = FastAPI(title="Analista B3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CAMINHO_ACOES = Path(exportar_web.PASTA_WEB) / "acoes.json"


@app.get("/api/status")
def status():
    """O SPA chama isso no boot para decidir se mostra o botao de atualizar."""
    return {
        "disponivel": True,
        "tem_dados": CAMINHO_ACOES.exists(),
    }


@app.post("/api/atualizar")
async def atualizar():
    """Raspa o Fundamentus de novo e regrava os JSON consumidos pelo SPA."""
    bruto = await asyncio.to_thread(coletar_fundamentus)
    acoes = filtrar_negociaveis(bruto)

    await asyncio.to_thread(salvar_csv, acoes, "fundamentus")
    await asyncio.to_thread(exportar_web.main)

    return {"ok": True, "total": len(acoes)}
