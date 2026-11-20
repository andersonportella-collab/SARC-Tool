# Publicação: GitHub, Streamlit Cloud e INPI

## 1. GitHub (organização andersonportella-collab)

1. Crie o repositório `SARC-Tool` em https://github.com/organizations/andersonportella-collab/repositories/new
   (privado até a publicação do artigo, se preferir; o Streamlit Community Cloud aceita repositórios privados
   da sua conta).
2. Na pasta `SARC-Tool`:
   ```bash
   git init -b main
   git add .
   git commit -m "SARC-Tool 1.0.0"
   git remote add origin https://github.com/andersonportella-collab/SARC-Tool.git
   git push -u origin main
   ```

## 2. Streamlit Community Cloud

1. Acesse https://share.streamlit.io, "Create app", escolha o repositório, branch `main`, arquivo `app.py`.
2. Python 3.11 ou 3.12 em "Advanced settings". Nenhum segredo é necessário: a chave da API é digitada pelo usuário.
3. Após o build, copie a URL e preencha `APP_URL` em `sarc/meta.py` e a seção "Acesso" dos READMEs.

## 3. Após a publicação do artigo

1. Em `sarc/meta.py`, preencha o dicionário `ARTICLE` (autores, título, periódico, volume, número, páginas, ano, DOI).
2. Atualize "Como citar" nos READMEs, os manuais em `docs/` e acrescente `preferred-citation` em `CITATION.cff`.
3. Se o repositório estava privado, torne-o público.

## 4. Registro no INPI

Checklist (https://www.gov.br/inpi/pt-br/servicos/programas-de-computador):
- [ ] Identificação dos autores e titulares (nome, CPF, endereço) e vínculo institucional (UFF, EGN)
- [ ] Título: SARC-Tool; data de criação: novembro de 2026; linguagem: Python
- [ ] Resumo digital hash do código-fonte (por exemplo, SHA-512 de um ZIP do repositório na versão registrada)
- [ ] Declaração de veracidade e GRU paga
- [ ] Após o registro, substitua `[BR512026010417-3]` em `sarc/meta.py`, READMEs, manuais e `CITATION.cff`
