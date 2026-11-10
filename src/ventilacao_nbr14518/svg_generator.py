"""Gerador de painel visual técnico infográfico em SVG (1440x900).

Representa os resultados do dimensionamento de exaustão e ventilação
conforme ABNT NBR 14518:2020 com precisão geométrica e visual elegante.
"""

from __future__ import annotations

from html import escape
from typing import List

from ventilacao_nbr14518.exporters import _fmt_frac
from ventilacao_nbr14518.models import ResultadoCalculo


def gerar_painel_svg(r: ResultadoCalculo) -> str:
    """Renderiza um painel infográfico SVG completo de 1440x900 pixels."""
    nome_proj = escape(r.nome_projeto)
    localizacao = escape(r.localizacao)
    tipo_coifa_str = escape(r.tipo_coifa.upper())
    severidade_str = escape(r.severidade_dominante.upper())
    metodo_det = escape(r.metodo_determinante.upper())

    vazao_proj_fmt = _fmt_frac(r.vazao_projeto_m3_h, 0)
    vazao_proj_s_fmt = _fmt_frac(r.vazao_projeto_m3_s, 2)
    vazao_comp_fmt = _fmt_frac(r.vazao_compensacao_m3_h, 0)

    v_cap_fmt = _fmt_frac(r.vazao_captura_m3_h, 0)
    v_face_fmt = _fmt_frac(r.vazao_face_m3_h, 0)
    v_pot_fmt = _fmt_frac(r.vazao_potencia_m3_h, 0)

    p_total_pa = _fmt_frac(r.pressao_total_ventilador_pa, 0)
    p_total_mmca = _fmt_frac(r.pressao_total_ventilador_mmca, 1)
    p_est_pa = _fmt_frac(r.pressao_estatica_total_pa, 0)

    pot_eixo_kw = _fmt_frac(r.potencia_eixo_kw, 2)
    motor_cv = _fmt_frac(r.motor_comercial_cv, 2)

    d_circ = r.duto_sugerido.diametro_circular_mm
    v_circ = _fmt_frac(r.duto_sugerido.velocidade_circular_efetiva_m_s, 1)
    ret_w = r.duto_sugerido.retangular_largura_mm
    ret_h = r.duto_sugerido.retangular_altura_mm
    v_ret = _fmt_frac(r.duto_sugerido.velocidade_retangular_efetiva_m_s, 1)

    svg_linhas: List[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900">',
        '  <defs>',
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0b1320"/>',
        '      <stop offset="100%" stop-color="#1c2838"/>',
        '    </linearGradient>',
        '    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#1e2c3d" stop-opacity="0.95"/>',
        '      <stop offset="100%" stop-color="#14202e" stop-opacity="0.95"/>',
        '    </linearGradient>',
        '    <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#0284c7"/>',
        '      <stop offset="100%" stop-color="#06b6d4"/>',
        '    </linearGradient>',
        '    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#f59e0b"/>',
        '      <stop offset="100%" stop-color="#d97706"/>',
        '    </linearGradient>',
        '    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">',
        '      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35"/>',
        '    </filter>',
        '  </defs>',
        '  <style>',
        '    .title { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 26px; font-weight: 700; fill: #ffffff; }',
        '    .subtitle { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 14px; fill: #94a3b8; }',
        '    .card-title { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 13px; font-weight: 600; fill: #38bdf8; text-transform: uppercase; letter-spacing: 1px; }',
        '    .val-huge { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 38px; font-weight: 800; fill: #f8fafc; }',
        '    .val-unit { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: 500; fill: #cbd5e1; }',
        '    .label { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 13px; fill: #94a3b8; }',
        '    .val-norm { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 14px; font-weight: 600; fill: #e2e8f0; }',
        '    .badge { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 11px; font-weight: 700; fill: #ffffff; }',
        '  </style>',
        '',
        '  <!-- Fundo Principal -->',
        '  <rect width="1440" height="900" fill="url(#bg)"/>',
        '',
        '  <!-- Cabeçalho -->',
        '  <rect x="40" y="30" width="1360" height="85" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <rect x="40" y="30" width="6" height="85" rx="3" fill="url(#primaryGrad)"/>',
        f'  <text x="65" y="65" class="title">{nome_proj}</text>',
        f'  <text x="65" y="93" class="subtitle">ABNT NBR 14518:2020 · SISTEMAS DE VENTILAÇÃO E EXAUSTÃO PARA COZINHAS PROFISSIONAIS · {localizacao}</text>',
        f'  <rect x="1170" y="52" width="110" height="32" rx="6" fill="#0369a1"/>',
        f'  <text x="1225" y="73" text-anchor="middle" class="badge">COIFA {tipo_coifa_str}</text>',
        f'  <rect x="1290" y="52" width="95" height="32" rx="6" fill="#b45309"/>',
        f'  <text x="1337" y="73" text-anchor="middle" class="badge">{severidade_str}</text>',
        '',
        '  <!-- Cards Superiores de Métricas Principais -->',
        '  <!-- Card 1: Vazão de Projeto -->',
        '  <rect x="40" y="135" width="320" height="150" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <rect x="40" y="135" width="4" height="150" rx="2" fill="#0284c7"/>',
        '  <text x="60" y="165" class="card-title">Vazão de Projeto (Exaustão)</text>',
        f'  <text x="60" y="215" class="val-huge">{vazao_proj_fmt} <tspan class="val-unit">m³/h</tspan></text>',
        f'  <text x="60" y="245" class="label">Vazão Instantânea: <tspan class="val-norm">{vazao_proj_s_fmt} m³/s</tspan></text>',
        f'  <text x="60" y="265" class="label">Critério Determinante: <tspan class="val-norm">{metodo_det}</tspan></text>',
        '',
        '  <!-- Card 2: Ar de Compensação -->',
        '  <rect x="385" y="135" width="320" height="150" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <rect x="385" y="135" width="4" height="150" rx="2" fill="#06b6d4"/>',
        '  <text x="405" y="165" class="card-title">Ar de Compensação (Make-up)</text>',
        f'  <text x="405" y="215" class="val-huge">{vazao_comp_fmt} <tspan class="val-unit">m³/h</tspan></text>',
        f'  <text x="405" y="245" class="label">Taxa Adotada: <tspan class="val-norm">{_fmt_frac(r.vazao_compensacao_m3_h / r.vazao_projeto_m3_h * 100, 0)}% da Exaustão</tspan></text>',
        '  <text x="405" y="265" class="label">Regime: <tspan class="val-norm">Pressão Negativa (~ -5 Pa)</tspan></text>',
        '',
        '  <!-- Card 3: Pressão Total do Ventilador -->',
        '  <rect x="730" y="135" width="320" height="150" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <rect x="730" y="135" width="4" height="150" rx="2" fill="#f59e0b"/>',
        '  <text x="750" y="165" class="card-title">Pressão Total do Sistema</text>',
        f'  <text x="750" y="215" class="val-huge">{p_total_pa} <tspan class="val-unit">Pa</tspan></text>',
        f'  <text x="750" y="245" class="label">Carga Hidráulica: <tspan class="val-norm">{p_total_mmca} mmca</tspan></text>',
        f'  <text x="750" y="265" class="label">Pressão Estática: <tspan class="val-norm">{p_est_pa} Pa</tspan></text>',
        '',
        '  <!-- Card 4: Motor do Exaustor -->',
        '  <rect x="1075" y="135" width="325" height="150" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <rect x="1075" y="135" width="4" height="150" rx="2" fill="#10b981"/>',
        '  <text x="1095" y="165" class="card-title">Motor Elétrico Selecionado</text>',
        f'  <text x="1095" y="215" class="val-huge">{motor_cv} <tspan class="val-unit">cv</tspan></text>',
        f'  <text x="1095" y="245" class="label">Potência no Eixo: <tspan class="val-norm">{pot_eixo_kw} kW</tspan></text>',
        '  <text x="1095" y="265" class="label">Exaustor: <tspan class="val-norm">Centrífugo c/ Motor Externo</tspan></text>',
        '',
        '  <!-- Seção Central: Diagrama Esquemático da Instalação -->',
        '  <rect x="40" y="305" width="760" height="560" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <text x="65" y="335" class="card-title">Esquema Físico da Instalação e Linha de Cocção</text>',
        '',
        '  <!-- Representação Visual da Coifa, Bloco e Duto -->',
        '  <g transform="translate(65, 360)">',
        '    <!-- Duto de Exaustão Vertical -->',
        '    <rect x="300" y="20" width="80" height="120" fill="#334155" stroke="#475569" stroke-width="2"/>',
        '    <line x1="340" y1="20" x2="340" y2="140" stroke="#0284c7" stroke-width="2" stroke-dasharray="6,4"/>',
        '    <text x="400" y="70" class="label">Duto de Gordura Soldado (18 MSG)</text>',
        f'    <text x="400" y="90" class="val-norm">Ø {d_circ} mm ou {ret_w}x{ret_h} mm</text>',
        f'    <text x="400" y="110" class="label">Velocidade: {v_circ} m/s (faixa 10-12,5 m/s)</text>',
        '',
        '    <!-- Exaustor no topo -->',
        '    <circle cx="340" cy="20" r="30" fill="#1e293b" stroke="#10b981" stroke-width="3"/>',
        '    <text x="340" y="25" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="700" fill="#10b981">EXAUSTOR</text>',
        '',
        '    <!-- Coifa (Plenum e Coifa Trapezoide) -->',
        '    <polygon points="200,140 480,140 560,250 120,250" fill="#1e293b" stroke="#38bdf8" stroke-width="3"/>',
        f'    <text x="340" y="195" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="700" fill="#38bdf8">COIFA {tipo_coifa_str}</text>',
        f'    <text x="340" y="215" text-anchor="middle" class="label">{_fmt_frac(r.comprimento_coifa_m)}m x {_fmt_frac(r.largura_coifa_m)}m · Área: {_fmt_frac(r.area_face_coifa_m2)} m²</text>',
        '',
        '    <!-- Filtros de Chicana na Coifa -->',
        '    <line x1="160" y1="235" x2="520" y2="235" stroke="#f59e0b" stroke-width="6" stroke-dasharray="16,8"/>',
        '    <text x="340" y="245" text-anchor="middle" class="label" fill="#f59e0b">Filtros Inerciais de Chicana Metálicos (45°)</text>',
        '',
        '    <!-- Setas de Captura Térmica Ascendente -->',
        '    <path d="M 220 330 Q 240 290 260 265" stroke="#06b6d4" stroke-width="2" fill="none" stroke-dasharray="4,4"/>',
        '    <path d="M 340 330 Q 340 290 340 265" stroke="#06b6d4" stroke-width="2" fill="none" stroke-dasharray="4,4"/>',
        '    <path d="M 460 330 Q 440 290 420 265" stroke="#06b6d4" stroke-width="2" fill="none" stroke-dasharray="4,4"/>',
        f'    <text x="50" y="295" class="label">Altura Montagem: {_fmt_frac(r.altura_montagem_m)} m</text>',
        f'    <text x="50" y="315" class="label">Projeção: {_fmt_frac(r.projecao_coifa_m)} m</text>',
        '',
        '    <!-- Bloco de Cocção (Equipamentos) -->',
        '    <rect x="160" y="340" width="360" height="90" rx="4" fill="#0f172a" stroke="#64748b" stroke-width="2"/>',
        '    <text x="340" y="375" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="700" fill="#f1f5f9">BLOCO DE COCÇÃO INDUSTRIAL</text>',
        f'    <text x="340" y="398" text-anchor="middle" class="label">Dimensões: {_fmt_frac(r.comprimento_bloco_m)}m x {_fmt_frac(r.largura_bloco_m)}m · Potência Total: {_fmt_frac(r.potencia_total_kw)} kW</text>',
        '    <text x="340" y="418" text-anchor="middle" class="val-norm" fill="#f59e0b">Severidade: ' + severidade_str + '</text>',
        '  </g>',
        '',
        '  <!-- Seção Lateral Direita: Comparativo dos 3 Métodos Normativos -->',
        '  <rect x="825" y="305" width="575" height="270" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <text x="850" y="335" class="card-title">Comparativo dos Métodos de Vazão (NBR 14518)</text>',
        '',
        '  <!-- Linha Método 1 -->',
        '  <rect x="850" y="355" width="525" height="50" rx="8" fill="#1e293b"/>',
        '  <text x="865" y="375" class="val-norm">1. Velocidade de Captura no Perímetro</text>',
        f'  <text x="865" y="395" class="label">P_aberto = {_fmt_frac(r.perimetro_aberto_m)} m · H = {_fmt_frac(r.altura_montagem_m)} m</text>',
        f'  <text x="1355" y="385" text-anchor="end" class="val-huge" font-size="20">{v_cap_fmt} <tspan class="val-unit">m³/h</tspan></text>',
        '',
        '  <!-- Linha Método 2 -->',
        '  <rect x="850" y="415" width="525" height="50" rx="8" fill="#1e293b"/>',
        '  <text x="865" y="435" class="val-norm">2. Velocidade de Face da Coifa</text>',
        f'  <text x="865" y="455" class="label">Área Face = {_fmt_frac(r.area_face_coifa_m2)} m²</text>',
        f'  <text x="1355" y="445" text-anchor="end" class="val-huge" font-size="20">{v_face_fmt} <tspan class="val-unit">m³/h</tspan></text>',
        '',
        '  <!-- Linha Método 3 -->',
        '  <rect x="850" y="475" width="525" height="50" rx="8" fill="#1e293b"/>',
        '  <text x="865" y="495" class="val-norm">3. Potência Térmica dos Equipamentos</text>',
        f'  <text x="865" y="515" class="label">Potência = {_fmt_frac(r.potencia_total_kw)} kW instalados</text>',
        f'  <text x="1355" y="505" text-anchor="end" class="val-huge" font-size="20">{v_pot_fmt} <tspan class="val-unit">m³/h</tspan></text>',
        '',
        f'  <text x="850" y="555" class="label">Critério Normativo NBR 14518: <tspan class="val-norm" fill="#38bdf8">Maior valor adotado ({metodo_det}) + Margem de 10%</tspan></text>',
        '',
        '  <!-- Seção Lateral Direita Inferior: Recomendações e Conformidade -->',
        '  <rect x="825" y="595" width="575" height="270" rx="12" fill="url(#cardGrad)" filter="url(#shadow)"/>',
        '  <text x="850" y="625" class="card-title">Diretrizes de Segurança e Prevenção de Incêndio</text>',
        '  <text x="850" y="660" class="label">• <tspan class="val-norm">Duto de Gordura:</tspan> Chapa de aço soldado estanque (mín 1,21mm / 18 MSG).</text>',
        '  <text x="850" y="690" class="label">• <tspan class="val-norm">Filtros de Chicana:</tspan> Metálicos laváveis a 45° com dreno para calha coletora.</text>',
        '  <text x="850" y="720" class="label">• <tspan class="val-norm">Proteção Contra Incêndio:</tspan> Damper corta-fogo termofusível (140°C).</text>',
        '  <text x="850" y="750" class="label">• <tspan class="val-norm">Ar de Compensação:</tspan> Reposição de 85% para estabilidade térmica da cozinha.</text>',
        '  <text x="850" y="780" class="label">• <tspan class="val-norm">Exaustor Centrífugo:</tspan> Pás curvadas para trás, motor externo ao fluxo.</text>',
        f'  <text x="850" y="835" class="subtitle">Lofrano Tecnologia · ABNT NBR 14518:2020 · Aritmética 100% Racional Exata</text>',
        '</svg>',
    ]
    return "\n".join(svg_linhas) + "\n"
