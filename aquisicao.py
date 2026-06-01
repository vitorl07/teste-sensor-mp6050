import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# --- Configurações do Arduino ---
SERIAL_PORT = '#' # Porta do Arduino
BAUD_RATE = 500000
SAMPLE_RATE = 1000      # 1000 Hz (igual ao Arduino)
BUFFER_SIZE = 1024      # 1024 amostras para boa resolução na FFT

# --- Inicialização Serial ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Conectado à porta {SERIAL_PORT}...")
except:
    print("Erro ao abrir porta serial. Verifique a conexão e o nome da porta.")
    exit()

# Buffers usando DEQUE
buffers = {
    'ax': deque(maxlen=BUFFER_SIZE), 
    'ay': deque(maxlen=BUFFER_SIZE), 
    'az': deque(maxlen=BUFFER_SIZE),
    'a_sum': deque(maxlen=BUFFER_SIZE)  # Novo buffer para a Soma
}
eixos = ['ax', 'ay', 'az']

# --- Função de FFT com Janela de Hanning e Filtro de Graves ---
def calcular_fft(sinal):
    y = np.array(sinal)
    y = y - np.mean(y) # Remove DC
    
    # JANELA DE HANNING
    y = y * np.hanning(len(y)) 
    
    yf = np.fft.fft(y)
    xf = np.fft.fftfreq(BUFFER_SIZE, 1 / SAMPLE_RATE)
    
    idx = np.arange(BUFFER_SIZE // 2)
    xf_pos = xf[idx]
    magnitude = np.abs(yf[idx])
    
    # Filtro Passa-Alta
    magnitude[0:5] = 0 
    
    peak_idx = np.argmax(magnitude)
    peak_freq = xf_pos[peak_idx]
    
    return xf_pos, magnitude, peak_freq

# --- Configuração do Gráfico (Agora com 4 subgráficos 2x2) ---
plt.style.use('ggplot')
fig, axs = plt.subplots(2, 2, figsize=(14, 8))

# Atribuindo os eixos a variáveis para facilitar
ax_x = axs[0, 0]
ax_y = axs[0, 1]
ax_z = axs[1, 0]
ax_sum = axs[1, 1]

# Linhas Tempo
line_x, = ax_x.plot([], [], color='red', label='Eixo X')
line_y, = ax_y.plot([], [], color='green', label='Eixo Y')
line_z, = ax_z.plot([], [], color='blue', label='Eixo Z')
line_sum, = ax_sum.plot([], [], color='black', label='Soma (Magnitude)')

# Configuração eixos Tempo (Padronizando os gráficos)
for ax, titulo in [(ax_x, 'Aceleração X'), (ax_y, 'Aceleração Y'), (ax_z, 'Aceleração Z'), (ax_sum, 'Soma (Resultante)')]:
    ax.set_title(titulo)
    ax.set_xlabel('Amostras')
    ax.set_ylabel('Aceleração (m/s²)')
    ax.set_xlim(0, BUFFER_SIZE)
    ax.grid(True)
    ax.legend(loc='upper right')

# Texto de Pico da FFT no gráfico da Soma (Ajuda a não perder a info de rotação do motor)
freq_text = ax_sum.text(0.65, 0.85, '', transform=ax_sum.transAxes, fontsize=10,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Lista de todas as linhas para a animação
all_lines = [line_x, line_y, line_z, line_sum, freq_text]

def init():
    for line in all_lines:
        if hasattr(line, 'set_data'):
            line.set_data([], [])
    freq_text.set_text('')
    return all_lines

def update(frame):
    # 1. Leitura dos dados
    lines_read = 0
    max_lines_per_frame = 150 
    
    while ser.in_waiting > 0 and lines_read < max_lines_per_frame:
        lines_read += 1
        try:
            line = ser.readline().decode('utf-8').strip()
            values = line.split(',')
            
            if len(values) == 3:
                # Converte para float
                val_x = float(values[0])
                val_y = float(values[1])
                val_z = float(values[2])
                
                # Calcula a Soma (Magnitude / Resultante)
                # Fórmula padrão de vibração: sqrt(X² + Y² + Z²)
                val_sum = np.sqrt(val_x**2 + val_y**2 + val_z**2)
                
                # Se o líder quiser a soma matemática simples (X+Y+Z), comente a linha acima e use:
                # val_sum = val_x + val_y + val_z
                
                buffers['ax'].append(val_x)
                buffers['ay'].append(val_y)
                buffers['az'].append(val_z)
                buffers['a_sum'].append(val_sum)
                        
        except ValueError:
            continue

    # 2. Processamento se os buffers estiverem cheios
    if len(buffers['ax']) >= BUFFER_SIZE:
        
        x_data = range(BUFFER_SIZE)
        
        # Atualiza dados dos eixos
        line_x.set_data(x_data, list(buffers['ax']))
        line_y.set_data(x_data, list(buffers['ay']))
        line_z.set_data(x_data, list(buffers['az']))
        line_sum.set_data(x_data, list(buffers['a_sum']))
        
        # Ajusta eixo Y automaticamente para X, Y, Z (vão de negativo a positivo)
        for ax, key in [(ax_x, 'ax'), (ax_y, 'ay'), (ax_z, 'az')]:
            max_acc = np.max(np.abs(list(buffers[key])))
            if max_acc > 0: ax.set_ylim(-max_acc * 1.2, max_acc * 1.2)
                
        # Ajusta eixo Y para a Soma (Magnitude é sempre positiva, então de 0 ao máximo)
        max_sum = np.max(list(buffers['a_sum']))
        min_sum = np.min(list(buffers['a_sum']))
        if max_sum > 0: ax_sum.set_ylim(min_sum * 0.8, max_sum * 1.2)
        
        # Calcula FFT apenas para a Soma para mostrar a frequência de pico do motor
        _, _, peak_freq_sum = calcular_fft(buffers['a_sum'])
        freq_text.set_text(f'Pico Soma:\n{peak_freq_sum:.1f} Hz')

    return all_lines

ani = FuncAnimation(fig, update, init_func=init, blit=False, interval=50)

plt.tight_layout()
plt.show()

ser.close()
