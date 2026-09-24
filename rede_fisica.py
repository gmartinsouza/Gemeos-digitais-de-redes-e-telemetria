import time
import json
import random
import threading
import paho.mqtt.client as mqtt

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_TELEMETRIA = "projeto_gemeo_digital_redes/telemetria"
TOPIC_CONTROLE = "projeto_gemeo_digital_redes/controle"

NUM_TWINS = 3

# Estado por gêmeo
def make_estado():
    return {
        "trafego_entrada_mbps": 0,
        "modo_balanceamento": False,
        "link_1": {"capacidade": 50.0, "carga": 0.0, "perda_pacotes": 0.0},
        "link_2": {"capacidade": 50.0, "carga": 0.0, "perda_pacotes": 0.0},
        "cpu_pct": 0.0,
        "ram_pct": 0.0,
        "status": "OK",
        "stress_until": 0,
        "stress_intensity": 1.0
    }

twins = {f"twin-{i+1}": make_estado() for i in range(NUM_TWINS)}

def on_message(client, userdata, msg):
    comando = msg.payload.decode().strip()
    parts = comando.split()
    cmd = parts[0] if parts else ""
    target = parts[1] if len(parts) > 1 else None
    def apply_to(twin_name, twin_state):
        if cmd == "ATIVAR_BALANCEAMENTO":
            twin_state["modo_balanceamento"] = True
            print(f"[ATUADOR] {twin_name} Balanceamento ATIVADO (50/50).")
        elif cmd == "DESATIVAR_BALANCEAMENTO":
            twin_state["modo_balanceamento"] = False
            print(f"[ATUADOR] {twin_name} Balanceamento DESATIVADO (Apenas Link 1).")
        elif cmd == "STRESS":
            # STRESS <device|ALL> <duration_seconds> <intensity>
            duration = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10
            try:
                intensity = float(parts[3]) if len(parts) > 3 else 2.0
            except Exception:
                intensity = 2.0
            twin_state["stress_until"] = time.time() + duration
            twin_state["stress_intensity"] = intensity
            print(f"[ATUADOR] {twin_name} entrando em STRESS por {duration}s (intensidade={intensity}).")

    if target:
        # comando direcionado a um gêmeo específico
        twin = target
        if twin.upper() == "ALL":
            for t_name, t_state in twins.items():
                apply_to(t_name, t_state)
        elif twin in twins:
            apply_to(twin, twins[twin])
        else:
            print(f"Comando recebido para gêmeo desconhecido: {twin}")
    else:
        # aplica a todos
        for twin, state in twins.items():
            apply_to(twin, state)

client = mqtt.Client()

client.on_message = on_message

print("Conectando ao Broker MQTT...")
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC_CONTROLE)
client.loop_start()

print("Roteador Físico iniciado! Enviando telemetria contínua...\n")

try:
    while True:
        # publica telemetria para cada gêmeo
        for twin_id, state in twins.items():
            novo_trafego = random.uniform(30.0, 80.0)
            # se o twin estiver sob stress, amplifica o tráfego
            if state.get("stress_until", 0) > time.time():
                novo_trafego = novo_trafego * state.get("stress_intensity", 1.0)
            state["trafego_entrada_mbps"] = round(novo_trafego, 2)

            if state["modo_balanceamento"]:
                carga_l1 = novo_trafego / 2
                carga_l2 = novo_trafego / 2
            else:
                carga_l1 = novo_trafego
                carga_l2 = 0.0

            state["link_1"]["carga"] = round(min(carga_l1, state["link_1"]["capacidade"]), 2)
            state["link_1"]["perda_pacotes"] = round(max(0.0, carga_l1 - state["link_1"]["capacidade"]), 2)

            state["link_2"]["carga"] = round(min(carga_l2, state["link_2"]["capacidade"]), 2)
            state["link_2"]["perda_pacotes"] = round(max(0.0, carga_l2 - state["link_2"]["capacidade"]), 2)

            perda_total_pct = round(((state["link_1"]["perda_pacotes"] + state["link_2"]["perda_pacotes"]) / max(1.0, novo_trafego)) * 100, 1)

            # Simula uso de CPU e RAM
            state["cpu_pct"] = round(random.uniform(5.0, 95.0), 1)
            state["ram_pct"] = round(random.uniform(10.0, 95.0), 1)

            # Estado simples de saúde
            if perda_total_pct > 15 or state["cpu_pct"] > 92 or state["ram_pct"] > 96:
                state["status"] = "CRITICAL"
            elif perda_total_pct > 7 or state["cpu_pct"] > 85 or state["ram_pct"] > 90:
                state["status"] = "WARN"
            else:
                state["status"] = "OK"

            telemetria = {
                "device_id": twin_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "entrada_total": state["trafego_entrada_mbps"],
                "balanceamento_ativo": state["modo_balanceamento"],
                "link_1_carga": state["link_1"]["carga"],
                "link_1_perda": state["link_1"]["perda_pacotes"],
                "link_2_carga": state["link_2"]["carga"],
                "link_2_perda": state["link_2"]["perda_pacotes"],
                "perda_total_pct": perda_total_pct,
                "stress_active": state.get("stress_until", 0) > time.time(),
                "stress_remaining_s": max(0, int(state.get("stress_until", 0) - time.time())),
                "cpu_pct": state["cpu_pct"],
                "ram_pct": state["ram_pct"],
                "status": state["status"]
            }

            client.publish(TOPIC_TELEMETRIA, json.dumps(telemetria))
            print(f"[{telemetria['timestamp']}] {twin_id} -> Entrada: {telemetria['entrada_total']} Mbps | Perda: {telemetria['perda_total_pct']}% | CPU: {telemetria['cpu_pct']}% | RAM: {telemetria['ram_pct']}% | {telemetria['status']}")
            time.sleep(0.5)

        # pausa entre ciclos completos
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nEncerrando o simulador...")
    client.loop_stop()
    client.disconnect()