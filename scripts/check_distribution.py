#!/usr/bin/env python3
"""Script de verificação de sanidade dos artefatos de distribuição (sdist e wheel)."""

from __future__ import annotations

from pathlib import Path
import sys
import tarfile
import zipfile


def verificar_distribuicao() -> int:
    dist_dir = Path(__file__).resolve().parent.parent / "dist"
    if not dist_dir.exists():
        print(f"Erro: Diretório '{dist_dir}' não encontrado.", file=sys.stderr)
        return 1

    sdists = list(dist_dir.glob("*.tar.gz"))
    wheels = list(dist_dir.glob("*.whl"))

    if not sdists:
        print("Erro: Nenhum pacote sdist (*.tar.gz) encontrado em dist/.", file=sys.stderr)
        return 1
    if not wheels:
        print("Erro: Nenhum pacote wheel (*.whl) encontrado em dist/.", file=sys.stderr)
        return 1

    print(f"Verificando sdist: {sdists[0].name}")
    with tarfile.open(sdists[0], "r:gz") as tar:
        nomes = tar.getnames()
        print(f"  Total de arquivos no sdist: {len(nomes)}")
        arquivos_obrigatorios = ["pyproject.toml", "README.md", "LICENSE"]
        for obr in arquivos_obrigatorios:
            if not any(n.endswith(obr) for n in nomes):
                print(f"Erro no sdist: arquivo obrigatório '{obr}' ausente.", file=sys.stderr)
                return 1

    print(f"Verificando wheel: {wheels[0].name}")
    with zipfile.ZipFile(wheels[0], "r") as zf:
        nomes_whl = zf.namelist()
        print(f"  Total de arquivos no wheel: {len(nomes_whl)}")
        if not any("py.typed" in n for n in nomes_whl):
            print("Erro no wheel: 'py.typed' não encontrado.", file=sys.stderr)
            return 1
        if any(n.startswith("tests/") for n in nomes_whl):
            print("Erro no wheel: pasta 'tests/' incluída indevidamente no pacote binário.", file=sys.stderr)
            return 1

    print("\nArtefatos de distribuição sdist e wheel validados com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(verificar_distribuicao())
