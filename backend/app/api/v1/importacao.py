from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.client import get_supabase
from backend.app.services.excel_import import parse_excel

router = APIRouter(
    prefix="/admin/importacoes",
    tags=["importacoes"],
    dependencies=[Depends(require_admin_token)],
)

MAX_FILE_SIZE = 4 * 1024 * 1024  # 4 MB


@router.post("/processar/{tenant_id}")
async def processar_excel(tenant_id: UUID, arquivo: UploadFile = File(...)) -> dict:
    """Recebe o Excel preenchido e cria as avaliações no banco."""
    conteudo = await arquivo.read()
    if len(conteudo) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 4 MB.")

    try:
        semanas = parse_excel(conteudo)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao ler planilha: {e}")

    sb = get_supabase()
    criadas = 0
    ignoradas = 0
    erros: list[str] = []

    for s in semanas:
        # Verifica se já existe avaliação para essa data
        exists = sb.table("avaliacoes_semanais")\
            .select("id")\
            .eq("tenant_id", str(tenant_id))\
            .eq("semana_referencia", s["semana_referencia"])\
            .limit(1)\
            .execute()

        if exists.data:
            ignoradas += 1
            continue

        try:
            sb.table("avaliacoes_semanais").insert({
                "tenant_id":        str(tenant_id),
                "semana_referencia": s["semana_referencia"],
                "status":           s["status"],
                "valores":          s["valores"],
            }).execute()
            criadas += 1
        except Exception as e:
            erros.append(f"{s['semana_referencia']}: {e}")

    # Registra no log de importações
    sb.table("tenant_importacoes").insert({
        "tenant_id":           str(tenant_id),
        "tipo":                "primeira_carga",
        "origem_arquivo_nome": arquivo.filename or "upload.xlsx",
        "status":              "concluido" if not erros else "concluido_com_erros",
        "registros_processados": criadas,
        "registros_com_erro":  len(erros),
        "payload_resumo":      {"semanas_total": len(semanas), "ignoradas": ignoradas, "erros": erros[:10]},
    }).execute()

    return {
        "ok":       True,
        "criadas":  criadas,
        "ignoradas": ignoradas,
        "erros":    erros[:10],
        "total":    len(semanas),
    }
