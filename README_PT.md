# SARC-Tool

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-red)](https://streamlit.io)
[![Licença: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-green)](LICENSE)
[![INPI](https://img.shields.io/badge/INPI-BR%20XXXXXXXX--X-orange)]()

**Configuração adaptativa de ranking guiada por estabilidade (SARC).** Aplicativo web que executa o SARC sobre
uma matriz de decisão enviada pelo usuário, compara com TOPSIS, VIKOR, COPRAS e AHP-Gaussiano e exporta
tabelas, gráficos e um relatório de reprodutibilidade.

Read in English: [README.md](README.md)

## Acesso

Aplicativo online: *URL disponível após a implantação no Streamlit Community Cloud.*

## O que o app faz

1. **Entrada**: upload de CSV ou XLSX, ou o exemplo embutido (Ranking Universitário Folha 2026, reduzido).
   Escolha da coluna de nomes, dos critérios e da direção de cada um (benefício ou custo). Colunas constantes
   são descartadas e listadas. Dados ausentes nunca são imputados: apenas casos completos são usados, o número
   de linhas excluídas é informado, com aviso de que a exclusão pode enviesar. Opção de usar as N primeiras linhas.
2. **SARC**: normalização vetorial, vetores PSI, GMD e uniforme, malha regular do simplex de misturas com
   K = 50, 100 e 200, nós críticos, regiões de ranking constante, área P por contagem de células, fronteira,
   raio ρ, centro discreto, estabilidade LOAO (S_min, S_mean), seleção lexicográfica (P, S_min, S_mean, ρ) e
   teste de ambiguidade.
3. **Comparadores**: TOPSIS, VIKOR (v = 0,5), COPRAS (pesos normativos opcionais e reescala opcional de cada
   coluna para 0 a 100 pela nota máxima possível) e AHP-Gaussiano (porte do código R). Configurações fixas do
   SARC: PSI puro, GMD puro, uniforme e mistura baricêntrica.
4. **Referência (opcional)**: Spearman, τ-b de Kendall, coincidência nas 1, 3 e 5 primeiras, deslocamento médio
   e máximo, cinco maiores deslocamentos. A referência é contexto de comparação, não verdade de campo.
5. **Diagnósticos**: convergência entre os dois maiores K (assinatura, deslocamento de θ > 0,015, diferença de
   área > 0,01, apenas como alertas), nós críticos, ambiguidade, identificabilidade (colinearidade entre
   w^PSI − u e w^GMD − u, ρ pequeno, 2 ou menos critérios ativos, PSI praticamente uniforme).
6. **Gráficos** (matplotlib, rótulos em PT ou EN, escala de cinza opcional, PNG 300 dpi): mapa ternário das cinco
   maiores regiões, inclinação das posições, vetores de pesos, τ-b do LOAO, mapa de calor da correlação entre
   critérios, gráfico de teia dos perfis normalizados, mapa de calor da correlação entre métodos.
7. **Exportação**: CSV, XLSX (todas as tabelas), relatório de reprodutibilidade em JSON (parâmetros, versões das
   bibliotecas, hash SHA-256 dos dados, data e hora) e ZIP com tudo.
8. **Interpretação por IA (opcional)**: desligada por padrão. Só é ativada quando o usuário digita uma chave da
   API Anthropic na barra lateral. Apenas o resumo dos resultados é enviado; a matriz só é enviada com
   consentimento explícito.

## Limites (também exibidos no app)

- O núcleo é ordinalmente equivalente a uma soma ponderada: em cada θ, o ranking é o de uma soma ponderada de (1 − r_ij)².
- A área P é medida por contagem de células da malha. O centro é um nó da malha.
- Quando o PSI é praticamente uniforme, θ é fracamente identificável.
- O app não afirma que o SARC é superior a outros métodos.

## Padrões congelados

| Parâmetro | Valor |
|---|---|
| Resoluções da malha K | 50, 100, 200 |
| Tolerância de nó crítico | 1e-10 |
| Tolerância de critério ativo | 1e-12 |
| Desempate do centro | 1e-15 |
| Tolerância de ambiguidade | 1e-12 |
| VIKOR v | 0,5 |
| τ-b | postos médios |

Limites da versão pública: até 300 alternativas e 30 critérios (aviso acima de 200 alternativas).

## Instalação local

```bash
git clone https://github.com/andersonportella-collab/SARC-Tool.git
cd SARC-Tool
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
streamlit run app.py
```

## Testes

```bash
pytest -q
```

Os testes reproduzem os resultados de referência do artigo (RUF 2026, 30 primeiras linhas): pesos PSI, GMD e
AHP-Gaussiano, SARC com K = 50, 100 e 200 (20.301 nós, 14 assinaturas, P = 0,362175, θ = (0,335; 0,320; 0,345)),
concordância com o ranking publicado para todos os métodos, subconjuntos Top 50 e 180 casos completos,
invariância de escala, extensão congelada para critérios de custo com zeros, leitura de dados, exportação e um
teste de fumaça do app.

## Autores

- **Anderson Gonçalves Portella**, Universidade Federal Fluminense (UFF), [ORCID 0000-0001-6520-4301](https://orcid.org/0000-0001-6520-4301)
- **Carlos Francisco Simões Gomes**, Universidade Federal Fluminense (UFF), [ORCID 0000-0002-6865-0275](https://orcid.org/0000-0002-6865-0275)
- **Marcos dos Santos**, Escola de Guerra Naval (EGN), [ORCID 0000-0003-1533-5535](https://orcid.org/0000-0003-1533-5535)

## Como citar

PORTELLA, A. G.; GOMES, C. F. S.; SANTOS, M. **SARC-Tool: configuração adaptativa de ranking guiada por
estabilidade**. Software, versão 1.0.0. Universidade Federal Fluminense; Escola de Guerra Naval, 2026. Registro
INPI: [BR XXXXXXXX-X]. Disponível em: https://github.com/andersonportella-collab/SARC-Tool.

Artigo: em preparação (a referência será incluída após a publicação). Veja também [CITATION.cff](CITATION.cff).

## Suporte

andersonportella@yahoo.com.br

## Licença

MIT. Veja [LICENSE](LICENSE).
