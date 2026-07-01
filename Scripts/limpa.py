"""
Filtro de colunas — rode este script NO SEU COMPUTADOR antes de enviar
os microdados do Censo da Educação Superior.

Objetivo: reduzir o tamanho do CSV mantendo apenas as colunas usadas
nas análises de evasão, modalidade, FIES e PROUNI, para ficar abaixo
do limite de 30 MB do upload no Claude.

Como usar:
1. Instale o pandas se ainda não tiver:
     pip install pandas

2. Ajuste a variável ARQUIVO_ENTRADA abaixo para o caminho do CSV
   baixado do INEP (ex.: "MICRODADOS_CADASTRO_CURSOS_2024.CSV").

3. Rode:
     python filtrar_colunas.py

4. Será gerado um arquivo "_FILTRADO.csv" bem menor. Envie esse
   arquivo para o Claude.
"""

import pandas as pd
import os

# ─────────────────────────────────────────────
# AJUSTE AQUI: caminho do arquivo original baixado do INEP
# ─────────────────────────────────────────────
ARQUIVO_ENTRADA = "microdados_censo_da_educacao_superior/MICRODADOS_CADASTRO_CURSOS_2009.CSV"

# ─────────────────────────────────────────────
# Colunas que mantemos (identificação + evasão + modalidade + FIES/PROUNI)
# Ajuste esta lista se precisar de outras colunas para a análise
# ─────────────────────────────────────────────
COLUNAS_MANTER = [
    # Identificação do curso e local de oferta
    "CO_IES", "CO_CURSO", "CO_MUNICIPIO", "SG_UF", "CO_REGIAO", "NO_REGIAO",
    "NO_CINE_ROTULO", "NO_CINE_AREA_GERAL",

    # Características do curso
    "TP_MODALIDADE_ENSINO", "TP_GRAU_ACADEMICO",
    "TP_ORGANIZACAO_ACADEMICA", "TP_CATEGORIA_ADMINISTRATIVA",

    # Quantitativos gerais (evasão)
    "QT_ING", "QT_MAT", "QT_CONC",

    # PROUNI
    "QT_ING_PROUNII", "QT_ING_PROUNIP",
    "QT_MAT_PROUNII", "QT_MAT_PROUNIP",
    "QT_CONC_PROUNII", "QT_CONC_PROUNIP",

    # FIES
    "QT_ING_FIES", "QT_MAT_FIES", "QT_CONC_FIES",
    "QT_ING_RPFIES", "QT_ING_NRPFIES",
    "QT_MAT_RPFIES", "QT_MAT_NRPFIES",
    "QT_CONC_RPFIES", "QT_CONC_NRPFIES",

    # Reserva de vagas / ações afirmativas
    "QT_ING_RESERVA_VAGA", "QT_ING_RVREDEPUBLICA",
    "QT_ING_RVPPI", "QT_ING_RVSOCIAL_RF", "QT_ING_RVPDEF",
    "QT_ING_RVETNICO"
]

# ─────────────────────────────────────────────
# LEITURA E FILTRO
# ─────────────────────────────────────────────
print(f"Lendo {ARQUIVO_ENTRADA}...")
df = pd.read_csv(ARQUIVO_ENTRADA, sep=";", encoding="latin1", low_memory=False)

print(f"Total de colunas no arquivo original: {len(df.columns)}")

# Mantém apenas as colunas que realmente existem no arquivo
# (evita erro caso alguma coluna não exista nesse ano específico)
colunas_existentes = [c for c in COLUNAS_MANTER if c in df.columns]
colunas_faltando = [c for c in COLUNAS_MANTER if c not in df.columns]

if colunas_faltando:
    print(f"\nAviso: estas colunas não existem neste arquivo e serão ignoradas:")
    for c in colunas_faltando:
        print(f"  - {c}")

df_filtrado = df[colunas_existentes]

# ─────────────────────────────────────────────
# SALVAR ARQUIVO FILTRADO
# ─────────────────────────────────────────────
nome_base = os.path.splitext(ARQUIVO_ENTRADA)[0]
arquivo_saida = f"{nome_base}_FILTRADO.csv"

df_filtrado.to_csv(arquivo_saida, sep=";", encoding="utf-8", index=False)

tamanho_original_mb = os.path.getsize(ARQUIVO_ENTRADA) / (1024 * 1024)
tamanho_filtrado_mb = os.path.getsize(arquivo_saida) / (1024 * 1024)

print(f"\nArquivo original: {tamanho_original_mb:.1f} MB")
print(f"Arquivo filtrado: {tamanho_filtrado_mb:.1f} MB ({arquivo_saida})")
print(f"Redução: {(1 - tamanho_filtrado_mb/tamanho_original_mb)*100:.0f}%")

if tamanho_filtrado_mb < 30:
    print("\nDentro do limite de 30 MB -- pode enviar para o Claude.")
else:
    print("\nAinda acima de 30 MB. Considere compactar em ZIP antes de enviar,")
    print("ou filtrar também as linhas (por exemplo, apenas uma UF ou área).")