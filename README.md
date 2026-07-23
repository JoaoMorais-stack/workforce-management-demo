# Workforce Management Demo

A privacy-safe portfolio application for managing a fictional workforce directory, weekly capacity and planned time off. It demonstrates how a lightweight operational tool can turn scattered staffing information into a clear, searchable and maintainable workspace.

> Status: functional portfolio demo. Every person, email address, department, role and location in the seeded database is fictional.

## Objective

Showcase a complete local web application with a responsive interface, a small JSON API, validated business rules and SQLite persistence, using only the Python standard library.

## Problem

Small teams often keep people, availability and planned absences in separate documents. That makes routine questions harder to answer: who is active, where capacity sits, which departments are represented and who will be away soon. This demo consolidates those workflows into one local dashboard.

## Features

- Operational dashboard with roster, active status, leave status and average weekly capacity.
- Department distribution and a rolling 30-day time-off view.
- Search by name, role or email.
- Filters for department and availability status.
- Create, inspect, update and remove fictional people records.
- Record multiple time-off periods with category and approval status.
- Responsive interface for desktop, tablet and mobile layouts.
- Automatic fictional seed data on the first run.
- Input validation, request-size limits and defensive static-file routing.

## Technologies

- Python 3.10 or newer.
- Python standard-library HTTP server.
- SQLite.
- Semantic HTML, modern CSS and vanilla JavaScript.
- `unittest` for automated coverage.

No third-party packages or build steps are required.

## Architecture

The application uses a small layered structure:

```text
Browser interface
       |
JSON API and static server
       |
Validation and business rules
       |
SQLite persistence
```

- `workforce_demo/server.py` handles HTTP routes, JSON responses and static assets.
- `workforce_demo/service.py` contains validation, queries and business operations.
- `workforce_demo/db.py` owns the schema and fictional seed records.
- `static/` contains the independent browser interface.
- `tests/` verifies core service behavior with temporary databases.

## Installation

1. Install Python 3.10 or newer.
2. Clone or download this repository.
3. Open a terminal in the project directory.

There are no external dependencies to install. The empty `requirements.txt` documents that decision.

## Running

```powershell
python app.py
```

On Windows, you can also run:

```powershell
.\run.bat
```

Open `http://127.0.0.1:5000` in a browser. The SQLite database is created at `data/workforce_demo.db` on first use.

Optional environment variables:

```powershell
$env:WORKFORCE_HOST = "127.0.0.1"
$env:WORKFORCE_PORT = "5050"
$env:WORKFORCE_DB_PATH = "C:\path\to\demo.db"
python app.py
```

## Demonstration

1. Review the operational metrics and department distribution.
2. Search for `Engineer` or filter by `Operations`.
3. Select a person to inspect their profile and planned time off.
4. Add a new fictional record using an `example.com` email address.
5. Edit capacity or add a time-off period and observe the dashboard refresh.

To return to a pristine demonstration, stop the application, delete the local `data/workforce_demo.db` file and start it again. The fictional seed dataset will be recreated automatically.

## Project Structure

```text
workforce-management-demo/
|-- app.py
|-- run.bat
|-- workforce_demo/
|   |-- __init__.py
|   |-- db.py
|   |-- server.py
|   `-- service.py
|-- static/
|   |-- index.html
|   |-- styles.css
|   `-- app.js
|-- tests/
|   |-- __init__.py
|   `-- test_service.py
|-- data/
|   `-- .gitkeep
|-- .gitignore
|-- LICENSE
`-- requirements.txt
```

## Limitations

- This is a single-user local demonstration, not a production HR system.
- Authentication, authorization, audit history and database migrations are not included.
- The application is designed for a small demo dataset and has no pagination.
- Time-off information is descriptive and does not implement policy calculations.
- The built-in HTTP server is appropriate for local evaluation only.

## Security and Privacy

- Seed records are fabricated and use reserved `example.com` addresses.
- The server binds to `127.0.0.1` by default.
- Database files, logs and environment files are excluded from version control.
- Inputs have allowlists, length limits and date validation.
- HTTP responses include restrictive content and browser security headers.
- Do not enter real personal, confidential or regulated information into this portfolio demo.

## Status

Version `1.0.0` is functional and testable. Core directory, dashboard, filtering and time-off workflows are implemented.

## Next Steps

- Add optional sign-in and role-based permissions.
- Add pagination and CSV import/export for synthetic datasets.
- Add database migration support.
- Expand API-level and browser-level automated tests.
- Package the application for a managed demo environment.

## Usage Rights

This repository is source-available for portfolio review only. It is not open source. See [LICENSE](LICENSE) for the complete terms.

---

# Demonstração de Gestão de Equipes

Aplicação de portfólio segura para privacidade, criada para administrar um diretório fictício de profissionais, capacidade semanal e ausências planejadas. O projeto demonstra como uma ferramenta operacional leve pode transformar informações dispersas em um ambiente claro, pesquisável e fácil de manter.

> Status: demonstração funcional para portfólio. Todas as pessoas, endereços de e-mail, áreas, funções e localidades do banco inicial são fictícios.

## Objetivo

Apresentar uma aplicação web local completa, com interface responsiva, pequena API JSON, regras de negócio validadas e persistência SQLite, usando somente a biblioteca padrão do Python.

## Problema

Equipes pequenas costumam manter informações de profissionais, disponibilidade e ausências em documentos separados. Isso dificulta respostas rotineiras: quem está ativo, onde está a capacidade, quais áreas estão representadas e quem ficará ausente em breve. Esta demonstração reúne esses fluxos em um único painel local.

## Funcionalidades

- Painel operacional com total de pessoas, disponibilidade e capacidade semanal média.
- Distribuição por área e agenda de ausências para os próximos 30 dias.
- Pesquisa por nome, função ou e-mail.
- Filtros por área e status de disponibilidade.
- Criação, consulta, atualização e remoção de registros fictícios.
- Cadastro de múltiplos períodos de ausência, com categoria e status de aprovação.
- Interface responsiva para computadores, tablets e celulares.
- Dados fictícios criados automaticamente na primeira execução.
- Validação de entradas, limite de requisições e proteção de caminhos de arquivos estáticos.

## Tecnologias

- Python 3.10 ou mais recente.
- Servidor HTTP da biblioteca padrão do Python.
- SQLite.
- HTML semântico, CSS moderno e JavaScript puro.
- `unittest` para testes automatizados.

Nenhum pacote de terceiros ou etapa de compilação é necessário.

## Arquitetura

O aplicativo usa uma estrutura simples em camadas:

```text
Interface no navegador
        |
API JSON e servidor de arquivos
        |
Validação e regras de negócio
        |
Persistência SQLite
```

- `workforce_demo/server.py` atende rotas HTTP, respostas JSON e arquivos estáticos.
- `workforce_demo/service.py` concentra validações, consultas e operações.
- `workforce_demo/db.py` define o banco e os registros fictícios iniciais.
- `static/` contém a interface independente do navegador.
- `tests/` verifica os comportamentos centrais com bancos temporários.

## Instalação

1. Instale o Python 3.10 ou mais recente.
2. Clone ou baixe este repositório.
3. Abra um terminal na pasta do projeto.

Não existem dependências externas para instalar. O arquivo `requirements.txt` vazio documenta essa decisão.

## Execução

```powershell
python app.py
```

No Windows, também é possível executar:

```powershell
.\run.bat
```

Acesse `http://127.0.0.1:5000` no navegador. O banco SQLite será criado em `data/workforce_demo.db` no primeiro uso.

As variáveis de ambiente opcionais estão documentadas no exemplo em inglês acima.

## Demonstração

1. Consulte os indicadores operacionais e a distribuição por área.
2. Pesquise por `Engineer` ou filtre por `Operations`.
3. Selecione uma pessoa para consultar perfil e ausências planejadas.
4. Adicione um registro fictício usando um endereço do domínio `example.com`.
5. Edite a capacidade ou adicione uma ausência e observe a atualização do painel.

Para restaurar a demonstração, encerre o aplicativo, exclua o arquivo local `data/workforce_demo.db` e inicie novamente. O conjunto fictício será recriado automaticamente.

## Estrutura do Projeto

A árvore completa de arquivos está documentada na versão em inglês acima.

## Limitações

- Esta é uma demonstração local para uma pessoa, não um sistema de RH em produção.
- Autenticação, permissões por perfil, histórico de alterações e migrações de banco não estão incluídos.
- O aplicativo foi projetado para poucos registros demonstrativos e não possui paginação.
- As ausências são descritivas e não executam cálculos de políticas internas.
- O servidor HTTP integrado é adequado somente para avaliação local.

## Segurança e Privacidade

- Os registros iniciais são inventados e usam endereços reservados do domínio `example.com`.
- O servidor escuta apenas `127.0.0.1` por padrão.
- Bancos, logs e arquivos de ambiente não entram no controle de versão.
- As entradas possuem listas permitidas, limites de tamanho e validação de datas.
- As respostas HTTP incluem cabeçalhos restritivos de conteúdo e segurança do navegador.
- Não insira informações pessoais reais, confidenciais ou regulamentadas nesta demonstração.

## Status

A versão `1.0.0` está funcional e pode ser testada. Os fluxos centrais de diretório, painel, filtros e ausências estão implementados.

## Próximos Passos

- Adicionar acesso opcional com permissões por perfil.
- Adicionar paginação e importação/exportação CSV para conjuntos sintéticos.
- Adicionar suporte a migrações de banco.
- Ampliar testes de API e de navegador.
- Empacotar o aplicativo para um ambiente gerenciado de demonstração.

## Direitos de Uso

Este repositório disponibiliza o código somente para avaliação de portfólio. Não é um projeto de código aberto. Consulte [LICENSE](LICENSE) para os termos completos.
