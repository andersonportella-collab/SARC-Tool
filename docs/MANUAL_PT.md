# SARC-Tool: Manual do Usuário

**Versão:** 1.0.0 · **Data:** novembro de 2026 · **Registro INPI:** [BR XXXXXXXX-X] · **Licença:** MIT
**Código:** https://github.com/andersonportella-collab/SARC-Tool · **Suporte:** andersonportella@yahoo.com.br

## 1. Finalidade

O SARC-Tool executa o método SARC (Stability-guided Adaptive Ranking Configuration) sobre uma matriz de decisão
(alternativas nas linhas, critérios nas colunas). O SARC combina três vetores de pesos derivados dos dados (PSI,
GMD e uniforme), explora todas as misturas desses vetores em uma malha do simplex e escolhe a configuração cuja
região de ranking constante tem maior área e maior estabilidade ao remover alternativas (LOAO). O app também
calcula TOPSIS, VIKOR, COPRAS e AHP-Gaussiano para comparação. Público: pesquisadores e analistas de decisão
multicritério.

## 2. Entrada de dados

### 2.1 Formato

Uma linha por alternativa e uma coluna por critério, com cabeçalho na primeira linha. CSV (separador `;` ou `,`,
decimal `,` ou `.`, detectados automaticamente) ou XLSX (primeira planilha). Exemplo:

| nome | custo | qualidade | prazo |
|---|---|---|---|
| A | 120 | 8,5 | 30 |
| B | 95 | 7,0 | 45 |

### 2.2 Passos na aba Dados

1. Escolha o exemplo embutido ou envie o arquivo.
2. Indique a coluna de nomes (opcional) e as colunas de critérios (somente numéricas aparecem).
3. Na tabela de configuração, defina a direção de cada critério: **benefício** (maior é melhor) ou **custo**
   (menor é melhor). Pesos normativos e nota máxima são opcionais e valem só para TOPSIS, VIKOR e COPRAS.
   Preencha todos ou nenhum.
4. Opcional: use apenas as N primeiras linhas; indique uma coluna de referência (nota ou posição).
5. Clique em **Executar análise**.

### 2.3 Tratamento automático

- Linhas com qualquer valor ausente nos critérios (ou na referência) são excluídas. Não há imputação. O app
  informa quantas linhas saíram e avisa que a exclusão pode enviesar a análise.
- Colunas constantes são descartadas e listadas.
- Critérios de custo usam 1/x na normalização. Se uma coluna de custo tiver zeros, usa-se a extensão congelada:
  1/√q para os q zeros e 0 para os demais.
- Limites da versão pública: 300 alternativas e 30 critérios. Para matrizes maiores, rode localmente.

## 3. Parâmetros

Padrões congelados (barra lateral, "Parâmetros avançados"): K = 50, 100 e 200; tolerância de nó crítico 1e-10;
tolerância de critério ativo 1e-12; desempate do centro 1e-15; ambiguidade 1e-12; VIKOR v = 0,5; τ-b com postos
médios. Alterações são registradas no relatório JSON. O resultado principal usa o maior K.

## 4. Resultados

### 4.1 Aba SARC

- **Área P**: fração do simplex ocupada pela região escolhida (contagem de células da malha).
- **S_min e S_mean**: menor e média dos τ-b entre o ranking original e o ranking recalculado sem cada alternativa.
  Valores próximos de 1 indicam ranking estável.
- **ρ**: distância do centro à fronteira da região no espaço de pesos efetivos.
- **θ**: coeficientes da mistura (PSI; GMD; uniforme) no centro.
- Tabelas: ranking SARC com posições de todos os métodos, cinco maiores regiões, resultados por K e vetores de pesos.

### 4.2 Aba Comparação

Posições por método, concordância com a referência (Spearman, τ-b, coincidência nas 1, 3 e 5 primeiras,
deslocamentos) e correlação entre métodos. A referência não é verdade de campo, e concordância não mede qualidade.

### 4.3 Aba Diagnósticos

Alertas (nunca excluem resultados): nós críticos, seleção ambígua, mudança de assinatura entre resoluções,
deslocamento de θ > 0,015, diferença de área > 0,01, PSI praticamente uniforme, colinearidade entre w^PSI − u e
w^GMD − u, ρ pequeno, 2 ou menos critérios ativos.

### 4.4 Aba Gráficos

(a) mapa ternário das cinco maiores regiões com o centro; (b) inclinação das posições entre métodos; (c) vetores
de pesos; (d) τ-b do LOAO por alternativa removida; (e) mapa de calor da correlação entre critérios; (f) gráfico
de teia dos perfis normalizados; (g) mapa de calor da correlação entre métodos. Escala de cinza e idioma dos
rótulos são configuráveis. Cada figura pode ser baixada em PNG 300 dpi.

### 4.5 Aba Exportar

CSV de cada tabela, XLSX com todas, relatório de reprodutibilidade em JSON (parâmetros, versões, hash SHA-256 dos
dados, data e hora) e ZIP com tabelas, figuras e relatório.

Os arquivos exportados são autossuficientes quanto a diagnósticos e concordância:

- **`alerts`**: uma linha por alerta, com `level`, `code`, `value` (valor medido ou contagem), `threshold`
  (limiar, quando houver) e `message_en` (mensagem em inglês). Sem alertas, a tabela vem só com o cabeçalho.
- **`convergence`**: além das colunas por K, a linha do maior K traz `theta_shift_vs_prev_K`,
  `area_diff_vs_prev_K`, `same_signature_vs_prev_K`, `theta_alert` e `area_alert`, que comparam com a resolução
  anterior. Nas demais linhas essas colunas ficam vazias.
- **`method_agreement`**: sempre criada, com ou sem referência. Uma linha por método, comparado ao ranking do
  SARC: τ-b, Spearman, coincidência nas 1, 3 e 5 primeiras, deslocamento médio e máximo.
- **`method_correlation` e `method_agreement`**: a primeira (e a figura g) traz a correlação de Spearman entre os
  rankings de todos os métodos; a segunda traz a τ-b de Kendall de cada método contra o SARC.
- No JSON, `summary.alerts` passou a ser uma lista de objetos `{level, code, value, threshold}`. A lista antiga de
  códigos continua em `summary.alerts_codes`, e `summary.method_agreement` traz a tabela acima.

### 4.6 Interpretação por IA (opcional)

Desligada por padrão. Na barra lateral, escolha o provedor, Anthropic (Claude) ou OpenAI (ChatGPT), e digite a
chave; surge a aba de interpretação. Modelos padrão: claude-sonnet-5-5 e gpt-4o-mini, ambos editáveis.
Somente o resumo dos resultados é enviado; a matriz só vai se você marcar o consentimento. A chave não é gravada.
Respostas de IA podem conter erros.

## 5. Exemplo passo a passo

1. Abra o app; o exemplo RUF 2026 já vem selecionado com as 30 primeiras linhas, critérios ens, pes, mer, ino,
   int (benefício), pesos 0,32; 0,42; 0,18; 0,04; 0,04, notas máximas 32, 42, 18, 4, 4 e referência `nota`.
2. Clique em Executar análise (alguns segundos).
3. Resultado esperado (K = 200): P = 0,3622; S_min = 0,9754; S_mean = 0,9947; θ = (0,335; 0,320; 0,345);
   sem nós críticos; mesma assinatura em K = 50, 100 e 200. Alerta: PSI praticamente uniforme.
4. Contra a nota publicada: SARC Spearman 0,866 e τ-b 0,692; TOPSIS 0,992 e 0,949; COPRAS 0,9996 e 0,995.

## 6. Limites do método

O núcleo é ordinalmente equivalente a uma soma ponderada; a área é medida por contagem de células; o centro é
discreto; a identificabilidade de θ é fraca quando PSI ≈ uniforme. O app não afirma superioridade do SARC.

## 7. Problemas comuns

| Problema | Causa provável | Solução |
|---|---|---|
| Nenhuma coluna numérica | decimal ou separador incomum | salve como CSV com `;` e decimal `,`, ou XLSX |
| Muitas linhas excluídas | valores ausentes | revise a planilha; o app não imputa |
| Resultado inesperado | direção benefício/custo trocada | revise a coluna Direção |
| AHP-Gaussiano ausente | zero em critério de custo | 1/x é indefinido; revise os dados |
| Matriz acima do limite | mais de 300 linhas ou 30 critérios | use N primeiras linhas ou rode localmente |

## 8. Referência e contato

Artigo metodológico: em preparação. Autores: Anderson Gonçalves Portella (UFF), Carlos Francisco Simões Gomes
(UFF), Marcos dos Santos (Escola de Guerra Naval). Suporte: andersonportella@yahoo.com.br.
