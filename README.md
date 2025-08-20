# PEP - Doutora Juliana Perez

Sistema local de Prontuário e Receitas (Flask + SQLite)

## Funcionalidades
- Cadastro de pacientes
- Busca por nome/CPF
- Registro de consultas (anamnese, exame físico, diagnóstico, conduta)
- Geração de **receitas em PDF** com cabeçalho personalizado
- Histórico de consultas e prescrições por paciente

## Requisitos
- Python 3.10 ou superior instalado no computador

## Como executar
1. Abra o terminal (Prompt de Comando / PowerShell no Windows, Terminal no macOS/Linux).
2. Vá até a pasta do projeto:
   ```bash
   cd pep_doutora_juliana_perez
   ```
3. (Opcional) Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
5. Inicie o sistema:
   ```bash
   python app.py
   ```
6. Acesse no navegador: http://127.0.0.1:5000

## Personalização
- Edite **settings.json** para alterar CRM, endereço, telefone, etc.
- Para incluir assinatura digital (imagem), salve um arquivo `static/assinatura.png`.
