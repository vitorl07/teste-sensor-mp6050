#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;

// Configurações para Baja
const int SAMPLE_RATE = 1000; // 1000 Hz para pegar frequências altas do motor
const unsigned long SAMPLE_INTERVAL = 1000 / SAMPLE_RATE; // 1 ms
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(500000); // Baud rate altíssimo
  
  if (!mpu.begin()) {
    Serial.println("Erro ao iniciar MPU6050!");
    while (1) { delay(10); }
  }

  // Escala de 16G para não saturar com a vibração do motor
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  
  // Giroscópio em 2000 graus/s (mesmo não enviando, precisa configurar)
  mpu.setGyroRange(MPU6050_RANGE_2000_DEG);
  
  // Filtro em 184Hz para deixar as frequências do motor passarem
  mpu.setFilterBandwidth(MPU6050_BAND_184_HZ); 
}

void loop() {
  unsigned long currentTime = micros(); // Micros para precisão de 1ms
  
  if (currentTime - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = currentTime;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    // Envia APENAS os 3 eixos do Acelerômetro para aliviar a porta serial
    Serial.print(a.acceleration.x); Serial.print(",");
    Serial.print(a.acceleration.y); Serial.print(",");
    Serial.println(a.acceleration.z); // ln no final para pular a linha
  }
}