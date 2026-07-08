from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.app.core.admin_auth import require_admin_token
from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.schemas.estrutura import (
    GrupoCreate, GrupoUpdate, GrupoResponse,
    LojaCreate, LojaUpdate, LojaResponse,
    GrupoComLojas, LojasArvoreResponse,
)

router = APIRouter(tags=["estrutura"])

# ---- Cliente: árvore para o seletor ----

@router.get("/me/lojas", response_model=LojasArvoreResponse)
def me_lojas(tenant_id: UUID = Depends(get_current_tenant)) -> LojasArvoreResponse:
    sb = get_supabase()
    t = sb.table("tenants").select("modo_rede").eq("id", str(tenant_id)).limit(1).execute()
    modo_rede = bool(t.data[0].get("modo_rede")) if t.data else False
    grupos = sb.table("grupos_economicos").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    lojas = sb.table("lojas").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    lojas_por_grupo: dict = {}
    for l in lojas:
        lojas_por_grupo.setdefault(l["grupo_id"], []).append(LojaResponse(**l))
    grupos_out = [GrupoComLojas(**g, lojas=lojas_por_grupo.get(g["id"], [])) for g in grupos]
    return LojasArvoreResponse(modo_rede=modo_rede, grupos=grupos_out)


# ---- Admin: CRUD estrutura ----
admin = APIRouter(prefix="/admin/tenants/{tenant_id}", dependencies=[Depends(require_admin_token)])


@admin.get("/grupos", response_model=list[GrupoResponse])
def listar_grupos(tenant_id: UUID) -> list[GrupoResponse]:
    rows = get_supabase().table("grupos_economicos").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    return [GrupoResponse(**r) for r in rows]


@admin.post("/grupos", response_model=GrupoResponse, status_code=201)
def criar_grupo(tenant_id: UUID, payload: GrupoCreate) -> GrupoResponse:
    data = {"tenant_id": str(tenant_id), "nome": payload.nome,
            "nivel_preenchimento": payload.nivel_preenchimento, "ordem": payload.ordem, "ativo": True}
    res = get_supabase().table("grupos_economicos").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar grupo.")
    return GrupoResponse(**res.data[0])


@admin.patch("/grupos/{gid}", response_model=GrupoResponse)
def atualizar_grupo(tenant_id: UUID, gid: UUID, payload: GrupoUpdate) -> GrupoResponse:
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not upd:
        raise HTTPException(status_code=400, detail="Nada para atualizar.")
    res = get_supabase().table("grupos_economicos").update(upd).eq("id", str(gid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return GrupoResponse(**res.data[0])


@admin.delete("/grupos/{gid}", status_code=204)
def excluir_grupo(tenant_id: UUID, gid: UUID) -> None:
    res = get_supabase().table("grupos_economicos").delete().eq("id", str(gid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")


@admin.get("/lojas", response_model=list[LojaResponse])
def listar_lojas(tenant_id: UUID) -> list[LojaResponse]:
    rows = get_supabase().table("lojas").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    return [LojaResponse(**r) for r in rows]


@admin.post("/lojas", response_model=LojaResponse, status_code=201)
def criar_loja(tenant_id: UUID, payload: LojaCreate) -> LojaResponse:
    data = {"tenant_id": str(tenant_id), "grupo_id": str(payload.grupo_id), "nome": payload.nome,
            "cnpj": payload.cnpj, "filial_excel": payload.filial_excel, "ordem": payload.ordem, "ativo": True}
    res = get_supabase().table("lojas").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar loja.")
    return LojaResponse(**res.data[0])


@admin.patch("/lojas/{lid}", response_model=LojaResponse)
def atualizar_loja(tenant_id: UUID, lid: UUID, payload: LojaUpdate) -> LojaResponse:
    upd = {k: (str(v) if k == "grupo_id" else v) for k, v in payload.model_dump().items() if v is not None}
    if not upd:
        raise HTTPException(status_code=400, detail="Nada para atualizar.")
    res = get_supabase().table("lojas").update(upd).eq("id", str(lid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")
    return LojaResponse(**res.data[0])


@admin.delete("/lojas/{lid}", status_code=204)
def excluir_loja(tenant_id: UUID, lid: UUID) -> None:
    res = get_supabase().table("lojas").delete().eq("id", str(lid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")


@admin.patch("/modo-rede")
def toggle_modo_rede(tenant_id: UUID, ativo: bool = Body(embed=True)) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    get_supabase().table("tenants").update({"modo_rede": ativo, "updated_at": now}).eq("id", str(tenant_id)).execute()
    return {"modo_rede": ativo}


router.include_router(admin)
