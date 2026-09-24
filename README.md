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



