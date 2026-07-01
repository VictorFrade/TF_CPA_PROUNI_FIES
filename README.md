# Efetividade do PROUNI e FIES na universalização da educação superior no Brasil
 
Projeto acadêmico de análise de dados públicos de educação, com foco em avaliar se os programas **PROUNI** e **FIES** ampliaram o acesso e a permanência de estudantes no ensino superior brasileiro.
 
## Questão de pesquisa
 
> Os programas de acesso ao ensino superior (PROUNI e FIES) ampliaram a participação de estudantes de baixa renda e de regiões menos desenvolvidas? Quais cursos, regiões e perfis de curso concentram os beneficiários, e como a evasão desses grupos se compara à evasão geral ao longo do tempo?
 
## Fonte dos dados
 
Todos os dados vêm do **Censo da Educação Superior**, publicado anualmente pelo INEP:
 
- Portal oficial: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior
- Dados do PROUNI e FIES específicos: https://dadosabertos.mec.gov.br
- Período coberto: **2009 a 2024** (15 pares de anos consecutivos, série contínua)
> **Nota sobre LGPD:** desde uma reestruturação motivada pela Lei Geral de Proteção de Dados, o INEP não disponibiliza mais o arquivo de vínculos individuais de alunos nos microdados públicos. Por isso, todas as análises deste projeto trabalham com dados **agregados por curso**, não por aluno individual — ver seção [Limitações metodológicas](#limitações-metodológicas).

## Metodologia
 
### Cálculo da taxa de evasão
 
Como os microdados públicos não têm identificador individual de aluno, a evasão é calculada em **nível agregado de curso**, pelo método oficial do INEP (fluxo agregado):
 
```
TE = 1 - (QT_CONC_t + QT_MAT_t) / (QT_ING_t + QT_MAT_t-1)
```
 
Onde `t` é o ano atual e `t-1` o ano anterior. Cursos com menos de 10 alunos na base de cálculo são descartados para evitar taxas instáveis (ex.: um único ingressante que evade geraria 100% de evasão).

### Análises realizadas
 
1. **Evasão média por modalidade de ensino** (presencial x EaD), grau acadêmico (bacharelado, licenciatura, tecnológico) e categoria administrativa (pública/privada), 2010–2024.
2. **Correlações PROUNI e FIES** — seis correlações específicas relacionando a proporção de beneficiários no curso, a evasão do subgrupo beneficiário e a evasão geral do curso.
3. **Correlações de políticas afirmativas** — proporção de ingressantes por reserva de vagas (total, escola pública, renda, étnico-racial, PCD) x evasão geral, com estratificação por setor administrativo, região e esfera pública.
## Principais achados
 
- **EaD evade sistematicamente mais que presencial** em todos os 15 anos da série, com a diferença se ampliando de ~0pp (2010) para ~14pp (2024).
- **Cursos tecnológicos evadem mais** que bacharelado e licenciatura em todos os anos, sem exceção.
- **IES privadas com fins lucrativos** têm evasão consistentemente mais alta que as públicas a partir de 2015, chegando a mais que o dobro da pública federal em 2024.
- **Bolsistas PROUNI evadem proporcionalmente menos** que a média geral do mesmo curso, padrão estável desde a implantação do programa (2010) até 2024.
- **O indicador de evasão específica do FIES é instável**, com valores negativos (metodologicamente inválidos) concentrados nos períodos de expansão/reformulação do programa (2010-2014 e 2023) — tratado como achado metodológico próprio, não como ruído aleatório.
- **A correlação entre cotas e menor evasão é, em grande parte, um efeito de composição**: ao controlar por categoria administrativa, o efeito quase desaparece nas IES privadas em toda a série, e só se torna forte nas públicas a partir de 2023–2024, liderado pelas públicas estaduais do Sudeste e Centro-Oeste — não um padrão nacional uniforme.
## Limitações metodológicas
 
- **Correlação ecológica, não causal.** Todas as correlações são calculadas em nível de curso (agregado), não de aluno individual.
- **Ausência de coluna de desfecho no FIES.** Quando o projeto usa arquivos de inscrição do FIES com ID individual, não é possível distinguir evasão real de conclusão antecipada, troca de curso ou descontinuação do financiamento — o indicador usado é de "não-permanência", não de evasão pura.
