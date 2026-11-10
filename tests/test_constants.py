"""Testes unitários para constantes e tabelas normativas da ABNT NBR 14518:2020."""

from __future__ import annotations

from fractions import Fraction
import unittest

from ventilacao_nbr14518.constants import (
    CLASSIFICACOES_SEVERIDADE,
    COEFICIENTES_SINGULARES_K,
    DENSIDADE_AR_PADRAO_KG_M3,
    KW_POR_CV,
    MARGEM_SEGURANCA_MOTOR,
    MOTORES_COMERCIAIS_CV,
    PA_POR_MMCA,
    PERDA_COIFA_PLENUM_PA,
    PERDA_DAMPER_CORTA_FOGO_PA,
    PERDA_DESCARGA_CHAPEU_PA,
    PERDA_FILTRO_CARVAO_ATIVADO_PA,
    PERDA_FILTRO_ELETROSTATICO_PA,
    PERDA_FILTRO_INERCIAL_CHICANA_PA,
    PERDA_UNITARIA_DUTO_PA_POR_M,
    RENDIMENTO_EXAUSTOR_PADRAO,
    TAXA_COMPENSACAO_PADRAO,
    TIPOS_COIFA,
    VELOCIDADE_DUTO_MAXIMA_M_S,
    VELOCIDADE_DUTO_MINIMA_M_S,
    VELOCIDADE_DUTO_RECOMENDADA_M_S,
)


class TestConstantes(unittest.TestCase):
    def test_severidades_definidas(self) -> None:
        chaves_esperadas = {"leve", "medio", "pesado", "extra_pesado"}
        self.assertEqual(set(CLASSIFICACOES_SEVERIDADE.keys()), chaves_esperadas)

    def test_severidades_sao_fracoes_positivas(self) -> None:
        for chave, sev in CLASSIFICACOES_SEVERIDADE.items():
            with self.subTest(chave=chave):
                self.assertIsInstance(sev.vazao_especifica_linear_min_m3_h_m, Fraction)
                self.assertGreater(sev.vazao_especifica_linear_min_m3_h_m, 0)
                self.assertIsInstance(sev.vazao_especifica_potencia_m3_h_kw, Fraction)
                self.assertGreater(sev.vazao_especifica_potencia_m3_h_kw, 0)
                self.assertIsInstance(sev.velocidade_captura_parede_m_s, Fraction)
                self.assertGreater(sev.velocidade_captura_parede_m_s, 0)
                self.assertIsInstance(sev.velocidade_captura_ilha_m_s, Fraction)
                self.assertGreater(sev.velocidade_captura_ilha_m_s, sev.velocidade_captura_parede_m_s)

    def test_tipos_coifa(self) -> None:
        chaves = {"parede", "ilha", "canto", "compensadora"}
        self.assertEqual(set(TIPOS_COIFA.keys()), chaves)
        for chave, tipo in TIPOS_COIFA.items():
            with self.subTest(tipo=chave):
                self.assertIsInstance(tipo.projecao_minima_m, Fraction)
                self.assertGreaterEqual(tipo.projecao_minima_m, Fraction(150, 1000))

    def test_motores_comerciais_ordem_crescente(self) -> None:
        self.assertGreater(len(MOTORES_COMERCIAIS_CV), 5)
        for i in range(len(MOTORES_COMERCIAIS_CV) - 1):
            self.assertLess(MOTORES_COMERCIAIS_CV[i], MOTORES_COMERCIAIS_CV[i + 1])

    def test_conversoes_fisicas_e_constantes(self) -> None:
        self.assertEqual(DENSIDADE_AR_PADRAO_KG_M3, Fraction(12, 10))
        self.assertEqual(VELOCIDADE_DUTO_MINIMA_M_S, Fraction(10, 1))
        self.assertEqual(VELOCIDADE_DUTO_RECOMENDADA_M_S, Fraction(11, 1))
        self.assertEqual(VELOCIDADE_DUTO_MAXIMA_M_S, Fraction(13, 1))
        self.assertEqual(TAXA_COMPENSACAO_PADRAO, Fraction(85, 100))
        self.assertEqual(RENDIMENTO_EXAUSTOR_PADRAO, Fraction(70, 100))
        self.assertEqual(MARGEM_SEGURANCA_MOTOR, Fraction(115, 100))
        self.assertEqual(KW_POR_CV, Fraction(73549875, 100000000))
        self.assertEqual(PA_POR_MMCA, Fraction(980665, 100000))

    def test_perdas_de_carga_positivas(self) -> None:
        self.assertGreater(PERDA_COIFA_PLENUM_PA, 0)
        self.assertGreater(PERDA_FILTRO_INERCIAL_CHICANA_PA, 0)
        self.assertGreater(PERDA_FILTRO_ELETROSTATICO_PA, 0)
        self.assertGreater(PERDA_FILTRO_CARVAO_ATIVADO_PA, 0)
        self.assertGreater(PERDA_DAMPER_CORTA_FOGO_PA, 0)
        self.assertGreater(PERDA_DESCARGA_CHAPEU_PA, 0)
        self.assertGreater(PERDA_UNITARIA_DUTO_PA_POR_M, 0)

    def test_coeficientes_singulares_k(self) -> None:
        for k_nome, k_val in COEFICIENTES_SINGULARES_K.items():
            with self.subTest(k=k_nome):
                self.assertIsInstance(k_val, Fraction)
                self.assertGreater(k_val, 0)


if __name__ == "__main__":
    unittest.main()
