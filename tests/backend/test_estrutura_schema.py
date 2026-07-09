from uuid import UUID
from backend.app.schemas.estrutura import (
    GrupoCreate, GrupoResponse, LojaCreate, LojaResponse,
    GrupoComLojas, LojasArvoreResponse,
)

TID = UUID("b2ce08a4-b1f9-4465-b162-9f5e9bb70092")
GID = UUID("11111111-1111-1111-1111-111111111111")
LID = UUID("22222222-2222-2222-2222-222222222222")


def test_grupo_create_default_nivel_loja():
    g = GrupoCreate(nome="Geral")
    assert g.nivel_preenchimento == "loja"
    assert g.ordem == 0


def test_grupo_create_nivel_grupo():
    g = GrupoCreate(nome="Consolidado", nivel_preenchimento="grupo")
    assert g.nivel_preenchimento == "grupo"


def test_loja_create_opcionais():
    l = LojaCreate(grupo_id=GID, nome="Loja 1")
    assert l.cnpj is None
    assert l.filial_excel is None


def test_arvore_response():
    grupo = GrupoComLojas(
        id=GID, tenant_id=TID, nome="Geral", nivel_preenchimento="loja",
        ordem=0, ativo=True,
        lojas=[LojaResponse(id=LID, tenant_id=TID, grupo_id=GID, nome="Loja 1",
                            cnpj=None, filial_excel=1, ordem=0, ativo=True)],
    )
    arvore = LojasArvoreResponse(modo_rede=True, grupos=[grupo])
    assert arvore.modo_rede is True
    assert arvore.grupos[0].lojas[0].nome == "Loja 1"
