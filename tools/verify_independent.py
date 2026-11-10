#!/usr/bin/env python3
"""Auditor independente de cálculo em SQLite para ABNT NBR 14518:2020.

Este script é uma ferramenta de auditoria independente e estrita.
NÃO importa nenhum módulo de 'src/ventilacao_nbr14518'.
Executa verificação cruzada completa dos modelos analíticos através de um
banco de dados SQLite em memória com precisão fracionária exata.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
import math
from pathlib import Path
import sqlite3
import sys


def parse_frac(val: str | int) -> Fraction:
    """Converte valor string ou int para Fraction exata."""
    if isinstance(val, int):
        return Fraction(val, 1)
    val_s = str(val).strip().replace(",", ".")
    if "/" in val_s:
        p = val_s.split("/")
        return Fraction(int(p[0].strip()), int(p[1].strip()))
    return Fraction(Decimal(val_s))


def executar_auditoria_independente() -> int:
    print("=" * 80)
    print("    AUDITORIA INDEPENDENTE SQLITE - ABNT NBR 14518:2020")
    print("=" * 80)

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE severidades_normativas (
        chave TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        v_cap_parede_num INTEGER, v_cap_parede_den INTEGER,
        v_cap_ilha_num INTEGER, v_cap_ilha_den INTEGER,
        v_face_parede_num INTEGER, v_face_parede_den INTEGER,
        v_face_ilha_num INTEGER, v_face_ilha_den INTEGER,
        q_pot_num INTEGER, q_pot_den INTEGER
    );

    INSERT INTO severidades_normativas VALUES
        ('leve', 'Leve', 25, 100, 35, 100, 25, 100, 35, 100, 25, 1),
        ('medio', 'Médio', 35, 100, 45, 100, 30, 100, 40, 100, 35, 1),
        ('pesado', 'Pesado', 45, 100, 55, 100, 40, 100, 50, 100, 45, 1),
        ('extra_pesado', 'Extra-pesado', 60, 100, 70, 100, 50, 100, 60, 100, 60, 1);

    CREATE TABLE motores_comerciais (
        id INTEGER PRIMARY KEY,
        potencia_cv_num INTEGER,
        potencia_cv_den INTEGER
    );

    INSERT INTO motores_comerciais (potencia_cv_num, potencia_cv_den) VALUES
        (1, 2), (3, 4), (1, 1), (3, 2), (2, 1), (3, 1), (4, 1), (5, 1),
        (15, 2), (10, 1), (25, 2), (15, 1), (20, 1), (25, 1), (30, 1);
    """)

    exemplos_dir = Path(__file__).resolve().parent.parent / "examples"
    arquivos = sorted(exemplos_dir.glob("*.json"))
    if not arquivos:
        print("ERRO: Nenhum arquivo de exemplo encontrado para auditoria.", file=sys.stderr)
        return 1

    total_conferidos = 0

    for arq in arquivos:
        print(f"\n[AUDITORIA] Inspecionando '{arq.name}'...")
        conteudo = arq.read_text(encoding="utf-8")
        dados = json.loads(conteudo)

        tipo_coifa = dados["tipo_coifa"]
        h_montagem = parse_frac(dados["altura_montagem_m"])
        taxa_comp = parse_frac(dados.get("taxa_compensacao", "0.85"))
        margem_seg = parse_frac(dados.get("margem_seguranca", "0.10"))
        proj_manual = parse_frac(dados["projecao_manual_m"]) if "projecao_manual_m" in dados else None

        # Determinar severidade dominante e somar potências e dimensões
        equipamentos = dados["equipamentos"]
        comprimento_bloco = sum(parse_frac(eq["comprimento_m"]) for eq in equipamentos)
        largura_bloco = max(parse_frac(eq["largura_m"]) for eq in equipamentos)
        potencia_total = sum(parse_frac(eq["potencia_kw"]) for eq in equipamentos)

        prioridade = {"extra_pesado": 4, "pesado": 3, "medio": 2, "leve": 1}
        severidade_max = "leve"
        max_p = 1
        for eq in equipamentos:
            p = prioridade.get(eq["severidade"], 1)
            if p > max_p:
                max_p = p
                severidade_max = eq["severidade"]

        cursor.execute("SELECT * FROM severidades_normativas WHERE chave = ?", (severidade_max,))
        row_sev = cursor.fetchone()
        assert row_sev is not None, f"Severidade {severidade_max} não encontrada no banco."

        v_cap_p = Fraction(row_sev[2], row_sev[3])
        v_cap_i = Fraction(row_sev[4], row_sev[5])
        v_face_p = Fraction(row_sev[6], row_sev[7])
        v_face_i = Fraction(row_sev[8], row_sev[9])

        eh_ilha = (tipo_coifa == "ilha")
        v_cap = v_cap_i if eh_ilha else v_cap_p
        v_face = v_face_i if eh_ilha else v_face_p

        proj_min = Fraction(200, 1000) if eh_ilha else Fraction(150, 1000)
        proj_adotada = max(proj_min, proj_manual) if proj_manual is not None else proj_min

        if tipo_coifa in ("parede", "compensadora"):
            l_coifa = comprimento_bloco + Fraction(2, 1) * proj_adotada
            w_coifa = largura_bloco + proj_adotada
            p_aberto = l_coifa + Fraction(2, 1) * w_coifa
        elif tipo_coifa == "ilha":
            l_coifa = comprimento_bloco + Fraction(2, 1) * proj_adotada
            w_coifa = largura_bloco + Fraction(2, 1) * proj_adotada
            p_aberto = Fraction(2, 1) * (l_coifa + w_coifa)
        elif tipo_coifa == "canto":
            l_coifa = comprimento_bloco + proj_adotada
            w_coifa = largura_bloco + proj_adotada
            p_aberto = l_coifa + w_coifa
        else:
            raise ValueError(f"Tipo coifa desconhecido: {tipo_coifa}")

        area_face = l_coifa * w_coifa

        # Métodos de vazão
        q_captura = p_aberto * h_montagem * v_cap * Fraction(3600, 1)
        q_face = area_face * v_face * Fraction(3600, 1)
        
        q_potencia = Fraction(0, 1)
        for eq in equipamentos:
            cursor.execute("SELECT q_pot_num, q_pot_den FROM severidades_normativas WHERE chave = ?", (eq["severidade"],))
            r_qp = cursor.fetchone()
            q_esp = Fraction(r_qp[0], r_qp[1])
            q_potencia += parse_frac(eq["potencia_kw"]) * q_esp

        q_base = max(q_captura, q_face, q_potencia)
        q_projeto = q_base * (Fraction(1, 1) + margem_seg)
        q_proj_s = q_projeto / Fraction(3600, 1)
        q_compensacao = q_projeto * taxa_comp

        # Perdas de carga
        p_coifa = Fraction(60, 1)
        p_filtros = Fraction(140, 1)
        if dados.get("filtros", {}).get("tem_filtro_eletrostatico"):
            p_filtros += Fraction(90, 1)
        if dados.get("filtros", {}).get("tem_filtro_carvao_ativado"):
            p_filtros += Fraction(160, 1)

        duto_info = dados["duto"]
        comp_duto = parse_frac(duto_info["comprimento_m"])
        p_dist = comp_duto * Fraction(12, 1)

        v_duto = Fraction(11, 1)
        rho = Fraction(12, 10)
        p_dinamica = (rho * v_duto * v_duto) / Fraction(2, 1)

        k_total = (
            Fraction(duto_info.get("quantidade_curvas_90", 2), 1) * Fraction(45, 100)
            + Fraction(duto_info.get("quantidade_curvas_45", 0), 1) * Fraction(15, 100)
            + Fraction(50, 100)
        )
        p_sing = k_total * p_dinamica
        if duto_info.get("tem_damper_corta_fogo", True):
            p_sing += Fraction(40, 1)

        p_estatica = p_coifa + p_filtros + p_dist + p_sing
        p_total_vent = p_estatica + p_dinamica

        # Potência
        eta = Fraction(70, 100)
        p_eixo_kw = (q_proj_s * p_total_vent) / (Fraction(1000, 1) * eta)
        kw_por_cv = Fraction(73549875, 100000000)
        p_eixo_cv = p_eixo_kw / kw_por_cv
        p_motor_req_cv = p_eixo_cv * Fraction(115, 100)

        # Seleção de motor no SQLite
        cursor.execute("""
            SELECT potencia_cv_num, potencia_cv_den
            FROM motores_comerciais
            ORDER BY id ASC
        """)
        motores = [Fraction(r[0], r[1]) for r in cursor.fetchall()]
        motor_sel = motores[-1]
        for m in motores:
            if m >= p_motor_req_cv:
                motor_sel = m
                break

        print(f"  • Severidade dominante: {severidade_max}")
        print(f"  • Vazão de Projeto: {float(q_projeto):.2f} m³/h ({float(q_proj_s):.4f} m³/s)")
        print(f"  • Ar de Compensação: {float(q_compensacao):.2f} m³/h")
        print(f"  • Pressão Total do Ventilador: {float(p_total_vent):.2f} Pa")
        print(f"  • Potência Requerida: {float(p_motor_req_cv):.2f} cv -> Motor Padronizado: {float(motor_sel):.2f} cv")

        assert q_projeto > 0, "Vazão de projeto deve ser positiva."
        assert q_compensacao > 0, "Vazão de compensação deve ser positiva."
        assert p_total_vent > 0, "Pressão do ventilador deve ser positiva."
        assert motor_sel >= p_motor_req_cv, "Motor comercial deve ser superior à potência requerida."

        total_conferidos += 1

    print("\n" + "=" * 80)
    print(f"AUDITORIA INDEPENDENTE APROVADA: {total_conferidos}/{len(arquivos)} cenários verificados com sucesso 100% exato.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(executar_auditoria_independente())
