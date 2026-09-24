Gêmeos Digitais - Simulador de Redes

Projeto de simulação com dois scripts:

- `rede_fisica.py`: simulador que publica telemetria MQTT de múltiplos gêmeos (routers) e recebe comandos de controle (`ATIVAR_BALANCEAMENTO`, `DESATIVAR_BALANCEAMENTO`, `STRESS`).
- `gemeo_digital.py`: dashboard em Streamlit que consome telemetria, exibe métricas e envia comandos de controle.

## Requisitos

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Como executar

1. Inicie o simulador:

```bash
python rede_fisica.py
```

2. Em outro terminal, execute o painel Streamlit:

```bash
streamlit run gemeo_digital.py
```

O painel irá mostrar os gêmeos conforme as mensagens MQTT chegarem.

## Comandos suportados (via tópico de controle MQTT)

- `ATIVAR_BALANCEAMENTO <device>` — ativa balanceamento no dispositivo alvo.
- `DESATIVAR_BALANCEAMENTO <device>` — desativa balanceamento.
- `STRESS <device|ALL> <duration_seconds> <intensity>` — aplica stress (aumenta tráfego) por `duration_seconds` segundos com fator `intensity`.

## Publicação no GitHub

1. Inicialize o repositório e faça commit:

```bash
git init
git add .
git commit -m "Initial commit: simulador e dashboard de gêmeos digitais"
```

2. Crie um repositório no GitHub (via web) e adicione o remote, ou use a CLI `gh`:

```bash
# Usando gh (opcional):
gh repo create <owner>/<repo-name> --public --source=. --push

# Ou manualmente (após criar repo na web):
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

Substitua `<owner>`/`<repo>` conforme seu usuário e nome de repositório.

---
Arquivo gerado automaticamente pelo assistente.
