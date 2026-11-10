"""Testes unitários para o motor de cálculo analítico da NBR 14518:2020."""

from __future__ import annotations

from fractions import Fraction
import unittest

from ventilacao_nbr14518.calculator import (
    _raiz_quadrada_fracao,
    calcular_dimensoes_duto_sugeridas,
    calcular_sistema_exaustao,
    determinar_severidade_dominante,
)
from ventilacao_nbr14518.models import (
    EntradaProjeto,
    EquipamentoCoccao,
    FiltrosSistema,
    TrechoDuto,
)


class TestCalculator(unittest.TestCase):
    def test_raiz_quadrada_fracao(self) -> None:
        self.assertEqual(_raiz_quadrada_fracao(Fraction(0, 1)), Fraction(0, 1))
        self.assertEqual(_raiz_quadrada_fracao(Fraction(4, 1)), Fraction(2, 1))
        self.assertEqual(_raiz_quadrada_fracao(Fraction(9, 16)), Fraction(3, 4))
        # Valor não exato: sqrt(2) ~ 1.414213
        r2 = _raiz_quadrada_fracao(Fraction(2, 1))
        self.assertAlmostEqual(float(r2), 1.414213, places=4)
        with self.assertRaises(ValueError):
            _raiz_quadrada_fracao(Fraction(-1, 1))

    def test_determinar_severidade_dominante(self) -> None:
        eq_leve = EquipamentoCoccao("Estufa", "leve", Fraction(5, 1), Fraction(1, 1), Fraction(1, 1))
        eq_medio = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        eq_pesado = EquipamentoCoccao("Charbroiler", "pesado", Fraction(25, 1), Fraction(1, 1), Fraction(1, 1))
        eq_extra = EquipamentoCoccao("Parrilha", "extra_pesado", Fraction(30, 1), Fraction(1, 1), Fraction(1, 1))

        self.assertEqual(determinar_severidade_dominante((eq_leve,)), "leve")
        self.assertEqual(determinar_severidade_dominante((eq_leve, eq_medio)), "medio")
        self.assertEqual(determinar_severidade_dominante((eq_leve, eq_medio, eq_pesado)), "pesado")
        self.assertEqual(determinar_severidade_dominante((eq_leve, eq_extra, eq_medio)), "extra_pesado")

    def test_calcular_dimensoes_duto(self) -> None:
        area = Fraction(25, 100)  # 0,25 m²
        vazao_s = Fraction(25, 10)  # 2,5 m³/s (~ 10 m/s)
        dim = calcular_dimensoes_duto_sugeridas(area, vazao_s)
        self.assertGreaterEqual(dim.diametro_circular_mm, 200)
        self.assertEqual(dim.diametro_circular_mm % 50, 0)
        self.assertGreaterEqual(dim.retangular_largura_mm, 200)
        self.assertEqual(dim.retangular_largura_mm % 50, 0)
        self.assertGreaterEqual(dim.retangular_altura_mm, 200)
        self.assertEqual(dim.retangular_altura_mm % 50, 0)
        self.assertIsInstance(dim.velocidade_circular_efetiva_m_s, Fraction)
        self.assertIsInstance(dim.velocidade_retangular_efetiva_m_s, Fraction)

    def test_calculo_coifa_parede_severidade_pesado(self) -> None:
        eq1 = EquipamentoCoccao("Charbroiler", "pesado", Fraction(25, 1), Fraction(12, 10), Fraction(85, 100))
        eq2 = EquipamentoCoccao("Fritadeira", "pesado", Fraction(22, 1), Fraction(5, 10), Fraction(85, 100))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1), quantidade_curvas_90=2)
        entrada = EntradaProjeto(
            nome_projeto="Cozinha Teste Parede",
            localizacao="São Paulo",
            tipo_coifa="parede",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(2, 10),  # 0,20 m
            equipamentos=(eq1, eq2),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)

        # Asserções de integridade analítica (zero floats)
        self.assertIsInstance(res.comprimento_bloco_m, Fraction)
        self.assertIsInstance(res.largura_bloco_m, Fraction)
        self.assertIsInstance(res.vazao_captura_m3_h, Fraction)
        self.assertIsInstance(res.vazao_face_m3_h, Fraction)
        self.assertIsInstance(res.vazao_potencia_m3_h, Fraction)
        self.assertIsInstance(res.vazao_projeto_m3_h, Fraction)
        self.assertIsInstance(res.vazao_compensacao_m3_h, Fraction)
        self.assertIsInstance(res.pressao_total_ventilador_pa, Fraction)
        self.assertIsInstance(res.potencia_eixo_kw, Fraction)
        self.assertIsInstance(res.motor_comercial_cv, Fraction)

        # Geometria
        self.assertEqual(res.comprimento_bloco_m, Fraction(17, 10))  # 1,20 + 0,50 = 1,70 m
        self.assertEqual(res.largura_bloco_m, Fraction(85, 100))    # 0,85 m
        self.assertEqual(res.projecao_coifa_m, Fraction(2, 10))     # 0,20 m
        self.assertEqual(res.comprimento_coifa_m, Fraction(21, 10)) # 1,70 + 2*0,20 = 2,10 m
        self.assertEqual(res.largura_coifa_m, Fraction(105, 100))   # 0,85 + 0,20 = 1,05 m
        self.assertEqual(res.perimetro_aberto_m, Fraction(42, 10))  # 2,10 + 2*1,05 = 4,20 m

        # Vazões positivas e coerentes
        self.assertGreater(res.vazao_captura_m3_h, 0)
        self.assertGreater(res.vazao_face_m3_h, 0)
        self.assertGreater(res.vazao_potencia_m3_h, 0)
        self.assertGreaterEqual(res.vazao_base_m3_h, res.vazao_captura_m3_h)
        self.assertGreaterEqual(res.vazao_base_m3_h, res.vazao_face_m3_h)
        self.assertGreaterEqual(res.vazao_base_m3_h, res.vazao_potencia_m3_h)
        self.assertEqual(res.vazao_projeto_m3_h, res.vazao_base_m3_h * Fraction(11, 10))
        self.assertEqual(res.vazao_compensacao_m3_h, res.vazao_projeto_m3_h * Fraction(85, 100))

        # Motor comercial
        self.assertGreaterEqual(res.motor_comercial_cv, res.potencia_motor_requerida_cv)

    def test_calculo_coifa_ilha(self) -> None:
        eq = EquipamentoCoccao("Fogão Central", "pesado", Fraction(40, 1), Fraction(2, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(15, 1))
        entrada = EntradaProjeto(
            nome_projeto="Cozinha Ilha",
            localizacao="RJ",
            tipo_coifa="ilha",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(25, 100),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)

        # Ilha projeta nos 4 lados:
        # L_coifa = 2.0 + 2*0.25 = 2.50 m
        # W_coifa = 1.0 + 2*0.25 = 1.50 m
        # P_aberto = 2 * (2.50 + 1.50) = 8.0 m
        self.assertEqual(res.comprimento_coifa_m, Fraction(25, 10))
        self.assertEqual(res.largura_coifa_m, Fraction(15, 10))
        self.assertEqual(res.perimetro_aberto_m, Fraction(8, 1))

    def test_projecao_minima_respeitada(self) -> None:
        # Tenta colocar projeção manual de 0,05 m em ilha (norma exige mínimo 0,20 m)
        eq = EquipamentoCoccao("Fogão", "leve", Fraction(10, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        entrada = EntradaProjeto(
            nome_projeto="Teste Projeção",
            localizacao="MG",
            tipo_coifa="ilha",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(5, 100),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)
        self.assertEqual(res.projecao_coifa_m, Fraction(200, 1000))

    def test_calculo_coifa_canto(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(25, 1), Fraction(15, 10), Fraction(9, 10))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        entrada = EntradaProjeto(
            nome_projeto="Cozinha Canto",
            localizacao="Porto Alegre",
            tipo_coifa="canto",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(15, 100),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)
        # Canto: 2 paredes, projeta em 2 lados livres
        # L_coifa = 1.5 + 0.15 = 1.65 m
        # W_coifa = 0.9 + 0.15 = 1.05 m
        # P_aberto = 1.65 + 1.05 = 2.70 m
        self.assertEqual(res.comprimento_coifa_m, Fraction(165, 100))
        self.assertEqual(res.largura_coifa_m, Fraction(105, 100))
        self.assertEqual(res.perimetro_aberto_m, Fraction(270, 100))

    def test_calculo_coifa_compensadora(self) -> None:
        eq = EquipamentoCoccao("Chapa e Fritadeira", "pesado", Fraction(40, 1), Fraction(2, 1), Fraction(9, 10))
        duto = TrechoDuto(comprimento_m=Fraction(12, 1))
        entrada = EntradaProjeto(
            nome_projeto="Cozinha Compensadora",
            localizacao="Brasília",
            tipo_coifa="compensadora",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(2, 10),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)
        self.assertIn("compensadora com insuflamento perimetral", " ".join(res.recomendacoes))

    def test_selecao_motor_limite_catalogo(self) -> None:
        # Equipamento de altíssima potência térmica para exigir motor de grande porte
        eq = EquipamentoCoccao("Churrasqueira Gigante", "extra_pesado", Fraction(300, 1), Fraction(8, 1), Fraction(15, 10))
        duto = TrechoDuto(comprimento_m=Fraction(60, 1), quantidade_curvas_90=6)
        entrada = EntradaProjeto(
            nome_projeto="Mega Churrascaria",
            localizacao="Goiânia",
            tipo_coifa="ilha",
            altura_montagem_m=Fraction(15, 10),
            projecao_manual_m=Fraction(3, 10),
            equipamentos=(eq,),
            duto=duto,
            filtros=FiltrosSistema(tem_filtro_inercial=True, tem_filtro_eletrostatico=True, tem_filtro_carvao_ativado=True),
        )
        res = calcular_sistema_exaustao(entrada)
        self.assertGreaterEqual(res.motor_comercial_cv, Fraction(20, 1))

    def test_tipo_coifa_invalido_gera_erro(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(10, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(5, 1))
        entrada = EntradaProjeto(
            nome_projeto="Teste",
            localizacao="SP",
            tipo_coifa="tipo_inexistente",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=None,
            equipamentos=(eq,),
            duto=duto,
        )
        with self.assertRaises(ValueError):
            calcular_sistema_exaustao(entrada)

    def test_descarga_veneziana_vs_chapeu(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        d1 = TrechoDuto(comprimento_m=Fraction(10, 1), tipo_descarga="saida_chapeu_chines")
        d2 = TrechoDuto(comprimento_m=Fraction(10, 1), tipo_descarga="descarga_direta_veneziana")
        ent1 = EntradaProjeto("P1", "SP", "parede", Fraction(1, 1), None, (eq,), d1)
        ent2 = EntradaProjeto("P2", "SP", "parede", Fraction(1, 1), None, (eq,), d2)

        res1 = calcular_sistema_exaustao(ent1)
        res2 = calcular_sistema_exaustao(ent2)
        # Veneziana tem K=0.70 vs Chapéu K=0.50
        self.assertGreater(res2.perda_duto_singular_pa, res1.perda_duto_singular_pa)


    def test_metodo_potencia_determinante(self) -> None:
        # Equipamento pequeno de altíssima potência térmica
        eq = EquipamentoCoccao("Wok Industrial Super", "pesado", Fraction(120, 1), Fraction(5, 10), Fraction(5, 10))
        duto = TrechoDuto(comprimento_m=Fraction(8, 1))
        entrada = EntradaProjeto(
            nome_projeto="Wok Station",
            localizacao="SP",
            tipo_coifa="parede",
            altura_montagem_m=Fraction(9, 10),
            projecao_manual_m=Fraction(15, 100),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)
        self.assertEqual(res.metodo_determinante, "potencia")

    def test_metodo_captura_determinante(self) -> None:
        # Bloco com equipamentos de baixa potência e grande perímetro
        eq = EquipamentoCoccao("Marmiteiro Aquecido", "leve", Fraction(5, 1), Fraction(3, 1), Fraction(8, 10))
        duto = TrechoDuto(comprimento_m=Fraction(8, 1))
        entrada = EntradaProjeto(
            nome_projeto="Linha Aquecimento",
            localizacao="SP",
            tipo_coifa="parede",
            altura_montagem_m=Fraction(12, 10),
            projecao_manual_m=Fraction(2, 10),
            equipamentos=(eq,),
            duto=duto,
        )
        res = calcular_sistema_exaustao(entrada)
        self.assertIn(res.metodo_determinante, ("captura", "face"))

    def test_recomendacoes_nbr14518_presentes(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1), tem_damper_corta_fogo=True)
        entrada = EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (eq,), duto)
        res = calcular_sistema_exaustao(entrada)
        texto_recs = " ".join(res.recomendacoes)
        self.assertIn("ABNT NBR 14518:2020", texto_recs)
        self.assertIn("Filtros inerciais", texto_recs)
        self.assertIn("Damper corta-fogo", texto_recs)


if __name__ == "__main__":
    unittest.main()
