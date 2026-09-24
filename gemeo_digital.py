import streamlit as st
import paho.mqtt.client as mqtt
import json
import queue
import pandas as pd
import time
import plotly.express as px

st.set_page_config(layout="wide", page_title="Gêmeo Digital de Redes")
st.title("Gêmeo Digital: Roteamento & Engenharia de Tráfego")

# Configurações MQTT
BROKER = "broker.emqx.io"
TOPIC_TELEMETRIA = "projeto_gemeo_digital_redes/telemetria"
TOPIC_CONTROLE = "projeto_gemeo_digital_redes/controle"

if 'fila_mensagens' not in st.session_state:
    st.session_state.fila_mensagens = queue.Queue()
if 'historico' not in st.session_state:
    # historico por device_id: cada entrada é um DataFrame
    st.session_state.historico = {}
if 'devices' not in st.session_state:
    st.session_state.devices = []

# Conecta ao MQTT
def iniciar_mqtt():
    if 'mqtt_client' not in st.session_state:
        client = mqtt.Client()
        q = st.session_state.fila_mensagens

        def on_connect(c, u, flags, rc):
            print(f"MQTT conectado (rc={rc})")
            try:
                c.subscribe(TOPIC_TELEMETRIA)
                print(f"Inscrito no tópico {TOPIC_TELEMETRIA}")
            except Exception as e:
                print("Erro ao subscrever:", e)

        def on_message(c, u, msg):
            try:
                payload = json.loads(msg.payload.decode())
            except Exception as e:
                print("Falha ao decodificar payload MQTT:", e)
                return
            q.put(payload)

        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(BROKER, 1883, 60)
        except Exception as e:
            st.error(f"Erro ao conectar no broker MQTT: {e}")
            return

        client.loop_start()
        st.session_state.mqtt_client = client
        st.session_state.mqtt_connected = True

iniciar_mqtt()

# Processa os dados que chegaram
while not st.session_state.fila_mensagens.empty():
    payload = st.session_state.fila_mensagens.get()
    device = payload.get('device_id', 'twin-1')

    if device not in st.session_state.historico:
        st.session_state.historico[device] = pd.DataFrame()
        st.session_state.devices.append(device)

    novo_df = pd.DataFrame([payload])
    st.session_state.historico[device] = pd.concat([st.session_state.historico[device], novo_df]).tail(100)

# Seleção do gêmeo
if st.session_state.devices:
    selected = st.selectbox("Selecionar Gêmeo", sorted(st.session_state.devices))
    dados_atuais = None
    if selected in st.session_state.historico and not st.session_state.historico[selected].empty:
        dados_atuais = st.session_state.historico[selected].iloc[-1].to_dict()
else:
    selected = None
    dados_atuais = None

# --- INTERFACE GRÁFICA ---
if dados_atuais:
    col_status, col_controle = st.columns([2, 1])

    with col_status:
        st.subheader("Estado da Rede (Tempo Real)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tráfego de Entrada", f"{dados_atuais.get('entrada_total', 'N/A')} Mbps")
        
        perda_cor = "🔴" if dados_atuais.get('perda_total_pct', 0) > 0 else "🟢"
        c2.metric(f"{perda_cor} Perda de Pacotes (Drop)", f"{dados_atuais.get('perda_total_pct', 0)}%")
        
        status_bal = "ATIVO (Link 1 + 2)" if dados_atuais.get('balanceamento_ativo', False) else "INATIVO (Apenas Link 1)"
        c3.metric("Balanceamento de Carga", status_bal)

        # Exibe CPU/RAM/Status
        cpu_col, ram_col, st_col = st.columns(3)
        cpu_col.metric("CPU", f"{dados_atuais.get('cpu_pct', 'N/A')}%")
        ram_col.metric("RAM", f"{dados_atuais.get('ram_pct', 'N/A')}%")
        st_col.metric("Status", dados_atuais.get('status', 'N/A'))
        # Indicador de stress (se o simulador publicar esse campo)
        if dados_atuais.get('stress_active', False):
            rem = dados_atuais.get('stress_remaining_s', 0)
            st.warning(f"🔥 Em Stress — {rem}s restantes")

    with col_controle:
        st.subheader("Ações do Gêmeo Digital")
        st.write("Atue sobre a rede emulada para corrigir falhas:")
        
        if dados_atuais.get('perda_total_pct', 0) > 5:
            st.error("⚠️ Alerta: Congestionamento Crítico Detectado!")
            
        if st.button("Ativar Balanceamento de Carga (Self-Healing)"):
            # Comando direcionado ao gêmeo selecionado
            if selected:
                st.session_state.mqtt_client.publish(TOPIC_CONTROLE, f"ATIVAR_BALANCEAMENTO {selected}")
        
        if st.button("Desativar Balanceamento (Reverter)"):
            if selected:
                st.session_state.mqtt_client.publish(TOPIC_CONTROLE, f"DESATIVAR_BALANCEAMENTO {selected}")

        st.write("---")
        dur = st.number_input("Duração do Stress (s)", min_value=1, max_value=600, value=10)
        intensity = st.slider("Intensidade do Stress", min_value=1.0, max_value=5.0, value=2.0, step=0.1)
        if st.button("Executar Stress Test no Gêmeo Selecionado"):
            if selected and 'mqtt_client' in st.session_state:
                cmd = f"STRESS {selected} {int(dur)} {float(intensity)}"
                st.session_state.mqtt_client.publish(TOPIC_CONTROLE, cmd)
                st.success(f"Comando enviado: {cmd}")
            else:
                st.error("Nenhum gêmeo selecionado ou MQTT desconectado.")

        st.write("---")
        st.write("Stress em todos os gêmeos:")
        dur_all = st.number_input("Duração (todos) (s)", min_value=1, max_value=600, value=8, key='dur_all')
        intensity_all = st.slider("Intensidade (todos)", min_value=1.0, max_value=5.0, value=1.8, step=0.1, key='int_all')
        if st.button("Executar Stress em Todos"):
            if 'mqtt_client' in st.session_state and st.session_state.devices:
                for dev in st.session_state.devices:
                    cmd = f"STRESS {dev} {int(dur_all)} {float(intensity_all)}"
                    st.session_state.mqtt_client.publish(TOPIC_CONTROLE, cmd)
                st.success(f"Stress enviado para {len(st.session_state.devices)} gêmeos.")
            else:
                st.error("MQTT desconectado ou nenhum gêmeo disponível.")

    st.divider()

    # Gráficos de Monitoramento
    df = st.session_state.historico.get(selected, pd.DataFrame())
    if not df.empty:
        fig_carga = px.line(df, x='timestamp', y=['link_1_carga', 'link_2_carga'],
                            title="Carga por Link (Capacidade Máxima: 50 Mbps/link)",
                            labels={'value': 'Banda Usada (Mbps)', 'variable': 'Interfaces'})

        fig_perda = px.line(df, x='timestamp', y='perda_total_pct',
                            title="Taxa de Perda de Pacotes (%)", color_discrete_sequence=['red'])

        fig_cpu = px.line(df, x='timestamp', y='cpu_pct', title="Uso CPU (%)")
        fig_ram = px.line(df, x='timestamp', y='ram_pct', title="Uso RAM (%)")

        st.plotly_chart(fig_carga, use_container_width=True)
        st.plotly_chart(fig_perda, use_container_width=True)
        st.plotly_chart(fig_cpu, use_container_width=True)
        st.plotly_chart(fig_ram, use_container_width=True)

else:
    st.info("Aguardando dados de telemetria da rede... (Execute o script rede_fisica.py)")

# Recarrega a tela a cada 1 segundo
time.sleep(1)
st.rerun()