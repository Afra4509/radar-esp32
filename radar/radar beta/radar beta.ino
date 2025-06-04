#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <NewPing.h>

// OLED Display Configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Sensor PIR Configuration
#define PIR_PIN 2
#define PIR_POWER_PIN 4

// Sensor Ultrasonik SF05 Configuration
#define TRIG_PIN 5
#define ECHO_PIN 18
#define MAX_DISTANCE 200 // Maximum distance in cm
#define DETECTION_THRESHOLD 50 // Detection threshold in cm

NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);

// System Variables
bool pir_detected = false;
bool ultrasonic_detected = false;
bool prev_pir_state = false;
bool prev_ultrasonic_state = false;

// PIR Enhanced Detection Variables - IMPROVED
unsigned long pir_detection_start = 0;
unsigned long pir_last_trigger = 0;
unsigned long pir_last_low = 0;
bool pir_active_phase = false;
bool pir_stabilizing = false;
int pir_trigger_count = 0;
int pir_consecutive_high = 0;
int pir_consecutive_low = 0;
const unsigned long PIR_ACTIVE_DURATION = 5000; // PIR stays active for 5 seconds
const unsigned long PIR_MIN_TRIGGER_INTERVAL = 50; // Minimum 50ms between triggers
const unsigned long PIR_RESET_TIMEOUT = 10000; // Reset counter after 10 seconds
const unsigned long PIR_STABILIZATION_TIME = 1000; // 1 second stabilization
const int PIR_MIN_CONSECUTIVE = 3; // Need 3 consecutive readings to confirm

// Ultrasonic Enhanced Detection Variables
int ultrasonic_readings[10] = {0};
int ultrasonic_index = 0;
int stable_readings_count = 0;
int detection_confidence = 0;
const int MIN_STABLE_READINGS = 5;
const int MAX_CONFIDENCE = 8;
const int CONFIDENCE_THRESHOLD = 3;

// Animation Variables
int animation_frame = 0;
unsigned long last_animation_time = 0;
unsigned long last_sensor_read = 0;
unsigned long last_status_send = 0;

// Timing Constants
const unsigned long ANIMATION_DELAY = 300; // Slower animation for better readability
const unsigned long SENSOR_READ_DELAY = 30; // Faster sensor reading
const unsigned long STATUS_SEND_DELAY = 100;

// Enhanced Debounce Variables
unsigned long last_pir_change = 0;
unsigned long last_ultrasonic_change = 0;
const unsigned long PIR_DEBOUNCE_DELAY = 30;
const unsigned long ULTRASONIC_DEBOUNCE_DELAY = 100;

// Calibration Variables
bool is_calibrating = false;
unsigned long calibration_start = 0;
int baseline_distance = 0;
const unsigned long CALIBRATION_DURATION = 3000;

// Display state management
enum DisplayState {
  IDLE,
  PIR_ONLY,
  ULTRASONIC_ONLY,
  BOTH_SENSORS,
  CALIBRATING
};
DisplayState current_display_state = IDLE;

void setup() {
  Serial.begin(115200);
  
  // Initialize OLED Display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    for(;;);
  }
  
  // Improved startup display
  displayStartupScreen();
  
  // Initialize PIR Sensor
  pinMode(PIR_PIN, INPUT);
  pinMode(PIR_POWER_PIN, OUTPUT);
  digitalWrite(PIR_POWER_PIN, HIGH);
  
  // Initialize Ultrasonic Sensor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Initialize ultrasonic readings array
  for(int i = 0; i < 10; i++) {
    ultrasonic_readings[i] = MAX_DISTANCE;
  }
  
  delay(2000); // Wait for PIR to stabilize
  
  // PIR stabilization period
  displayPIRStabilization();
  delay(PIR_STABILIZATION_TIME);
  
  // Start calibration
  startCalibration();
  
  Serial.println("SYSTEM_READY");
}

void loop() {
  unsigned long current_time = millis();
  
  // Handle calibration first
  if (is_calibrating) {
    handleCalibration();
    return;
  }
  
  // Handle serial commands
  handleSerialCommand();
  
  // Read sensors periodically
  if (current_time - last_sensor_read >= SENSOR_READ_DELAY) {
    readEnhancedSensors();
    last_sensor_read = current_time;
  }
  
  // Update display and send status
  if (current_time - last_status_send >= STATUS_SEND_DELAY) {
    updateDisplayState();
    updateDisplay();
    sendStatus();
    last_status_send = current_time;
  }
}

void displayStartupScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Header with border
  display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
  display.drawRect(2, 2, 124, 60, SSD1306_WHITE);
  
  // Title
  display.setTextSize(1);
  display.setCursor(10, 8);
  display.println("SISTEM DETEKSI OBJEK");
  
  // Version info
  display.setCursor(35, 20);
  display.println("Version 2.0");
  
  // Sensor info
  display.setCursor(15, 32);
  display.println("PIR + Ultrasonik");
  
  // Status
  display.setCursor(25, 44);
  display.println("Memulai sistem...");
  
  display.display();
  delay(2000);
}

void displayPIRStabilization() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Header
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  display.setCursor(20, 0);
  display.println("PIR STABILIZATION");
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
  
  display.setCursor(15, 20);
  display.println("Sensor PIR sedang");
  display.setCursor(25, 30);
  display.println("distabilkan...");
  
  display.setCursor(35, 45);
  display.println("Harap tunggu");
  
  // Loading animation
  for(int i = 0; i < 5; i++) {
    display.fillCircle(20 + i*15, 55, 2, SSD1306_WHITE);
  }
  
  display.display();
}

void startCalibration() {
  is_calibrating = true;
  calibration_start = millis();
  current_display_state = CALIBRATING;
  
  Serial.println("CALIBRATION_START");
}

void handleCalibration() {
  unsigned long elapsed = millis() - calibration_start;
  
  // Take baseline readings
  unsigned int distance = sonar.ping_cm();
  if (distance == 0) distance = MAX_DISTANCE;
  
  static int calibration_readings[30];
  static int cal_index = 0;
  static unsigned long last_reading_time = 0;
  
  // Take readings every 100ms
  if (millis() - last_reading_time >= 100 && cal_index < 30) {
    calibration_readings[cal_index] = distance;
    cal_index++;
    last_reading_time = millis();
  }
  
  // Improved calibration display
  displayCalibrationScreen(cal_index, 30);
  
  // Complete calibration
  if (cal_index >= 30 || elapsed >= CALIBRATION_DURATION) {
    // Calculate baseline
    long sum = 0;
    int valid_readings = max(1, cal_index);
    
    for (int i = 0; i < valid_readings; i++) {
      sum += calibration_readings[i];
    }
    baseline_distance = sum / valid_readings;
    
    // Reset static variables
    cal_index = 0;
    last_reading_time = 0;
    
    is_calibrating = false;
    Serial.print("CALIBRATION_COMPLETE:");
    Serial.println(baseline_distance);
    
    displayCalibrationComplete();
    delay(2000);
  }
}

void displayCalibrationScreen(int current_readings, int total_readings) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Header with border
  display.drawRect(0, 0, 128, 20, SSD1306_WHITE);
  display.setCursor(25, 6);
  display.println("KALIBRASI SENSOR");
  
  // Instructions
  display.setCursor(15, 25);
  display.println("Jangan bergerak!");
  
  // Progress info
  int progress = min(100, (current_readings * 100) / total_readings);
  display.setCursor(5, 35);
  display.print("Kemajuan: ");
  display.print(progress);
  display.println("%");
  
  display.setCursor(5, 45);
  display.print("Data: ");
  display.print(current_readings);
  display.print("/");
  display.println(total_readings);
  
  // Progress bar with border
  display.drawRect(5, 55, 118, 8, SSD1306_WHITE);
  display.fillRect(7, 57, (progress * 114) / 100, 4, SSD1306_WHITE);
  
  display.display();
}

void displayCalibrationComplete() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Success header
  display.drawRect(0, 0, 128, 20, SSD1306_WHITE);
  display.setCursor(20, 6);
  display.println("KALIBRASI SELESAI");
  
  // Checkmark
  display.drawLine(50, 25, 55, 30, SSD1306_WHITE);
  display.drawLine(55, 30, 65, 20, SSD1306_WHITE);
  display.drawCircle(57, 25, 8, SSD1306_WHITE);
  
  // Results
  display.setCursor(15, 40);
  display.print("Baseline: ");
  display.print(baseline_distance);
  display.println(" cm");
  
  display.setCursor(25, 50);
  display.println("Sistem siap!");
  
  display.display();
}

void readEnhancedSensors() {
  unsigned long current_time = millis();
  
  // IMPROVED PIR Reading with better noise filtering
  bool current_pir_raw = digitalRead(PIR_PIN);
  
  // Count consecutive readings
  if (current_pir_raw) {
    pir_consecutive_high++;
    pir_consecutive_low = 0;
  } else {
    pir_consecutive_low++;
    pir_consecutive_high = 0;
    pir_last_low = current_time;
  }
  
  // Determine PIR state based on consecutive readings
  bool pir_stable_high = (pir_consecutive_high >= PIR_MIN_CONSECUTIVE);
  bool pir_stable_low = (pir_consecutive_low >= PIR_MIN_CONSECUTIVE);
  
  // PIR Detection Logic
  if (pir_stable_high && !pir_active_phase && 
      (current_time - pir_last_trigger > PIR_MIN_TRIGGER_INTERVAL)) {
    pir_last_trigger = current_time;
    pir_trigger_count++;
    pir_active_phase = true;
    pir_detection_start = current_time;
  }
  
  // Maintain PIR active state
  if (pir_active_phase) {
    if (current_time - pir_last_trigger < PIR_ACTIVE_DURATION) {
      pir_detected = true;
    } else {
      pir_detected = false;
      pir_active_phase = false;
    }
  }
  
  // Reset trigger count after long inactivity
  if (current_time - pir_last_trigger > PIR_RESET_TIMEOUT) {
    pir_trigger_count = 0;
  }
  
  // Enhanced Ultrasonic Reading (unchanged but optimized)
  unsigned int distance = sonar.ping_cm();
  if (distance == 0) distance = MAX_DISTANCE;
  
  // Store reading in circular buffer
  ultrasonic_readings[ultrasonic_index] = distance;
  ultrasonic_index = (ultrasonic_index + 1) % 10;
  
  // Calculate median
  int median_distance = calculateMedianDistance();
  
  // Dynamic threshold
  int dynamic_threshold = min(DETECTION_THRESHOLD, max(20, baseline_distance - 15));
  
  // Confidence-based detection
  bool object_present = (median_distance > 0 && median_distance <= dynamic_threshold);
  
  if (object_present) {
    if (detection_confidence < MAX_CONFIDENCE) {
      detection_confidence++;
    }
  } else {
    if (detection_confidence > 0) {
      detection_confidence--;
    }
  }
  
  // Update detection state
  bool new_ultrasonic_state = (detection_confidence >= CONFIDENCE_THRESHOLD);
  
  if (new_ultrasonic_state != prev_ultrasonic_state && 
      (current_time - last_ultrasonic_change > ULTRASONIC_DEBOUNCE_DELAY)) {
    ultrasonic_detected = new_ultrasonic_state;
    prev_ultrasonic_state = new_ultrasonic_state;
    last_ultrasonic_change = current_time;
  }
}

int calculateMedianDistance() {
  int sorted_readings[10];
  for (int i = 0; i < 10; i++) {
    sorted_readings[i] = ultrasonic_readings[i];
  }
  
  // Simple bubble sort
  for (int i = 0; i < 9; i++) {
    for (int j = 0; j < 9 - i; j++) {
      if (sorted_readings[j] > sorted_readings[j + 1]) {
        int temp = sorted_readings[j];
        sorted_readings[j] = sorted_readings[j + 1];
        sorted_readings[j + 1] = temp;
      }
    }
  }
  
  return sorted_readings[5]; // Median
}

void updateDisplayState() {
  if (pir_detected && ultrasonic_detected) {
    current_display_state = BOTH_SENSORS;
  } else if (pir_detected) {
    current_display_state = PIR_ONLY;
  } else if (ultrasonic_detected) {
    current_display_state = ULTRASONIC_ONLY;
  } else {
    current_display_state = IDLE;
  }
}

void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  
  switch (current_display_state) {
    case BOTH_SENSORS:
      displayBothSensorsActive();
      break;
    case PIR_ONLY:
      displayPIRActive();
      break;
    case ULTRASONIC_ONLY:
      displayUltrasonicActive();
      break;
    case IDLE:
      displayIdleScreen();
      break;
    case CALIBRATING:
      // Handled in calibration function
      return;
  }
  
  display.display();
}

void displayBothSensorsActive() {
  // Animated border for maximum alert
  bool blink = ((millis() / 200) % 2);
  if (blink) {
    display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
    display.drawRect(2, 2, 124, 60, SSD1306_WHITE);
  }
  
  // Header
  display.setTextSize(1);
  display.setCursor(15, 6);
  display.println("DETEKSI MAKSIMAL!");
  
  // Large alert text
  display.setTextSize(2);
  display.setCursor(25, 20);
  display.println("KEDUA");
  display.setCursor(20, 38);
  display.println("SENSOR");
  
  // Status indicators
  display.setTextSize(1);
  display.setCursor(5, 55);
  display.print("PIR:ON  US:ON");
  
  // Corner indicators
  if (blink) {
    display.fillRect(0, 0, 8, 8, SSD1306_WHITE);
    display.fillRect(120, 0, 8, 8, SSD1306_WHITE);
    display.fillRect(0, 56, 8, 8, SSD1306_WHITE);
    display.fillRect(120, 56, 8, 8, SSD1306_WHITE);
  }
}

void displayPIRActive() {
  // Header with border
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(25, 2);
  display.println("SENSOR PIR AKTIF");
  display.drawLine(0, 14, 128, 14, SSD1306_WHITE);
  
  // Motion icon
  display.fillCircle(20, 30, 3, SSD1306_WHITE);
  display.drawCircle(20, 30, 6, SSD1306_WHITE);
  display.drawCircle(20, 30, 9, SSD1306_WHITE);
  
  // Status text
  display.setTextSize(1);
  display.setCursor(35, 25);
  display.println("GERAKAN");
  display.setCursor(35, 35);
  display.println("TERDETEKSI");
  
  // Statistics
  display.setCursor(5, 48);
  display.print("Triggers: ");
  display.println(pir_trigger_count);
  
  display.setCursor(5, 56);
  display.print("Durasi: ");
  display.print((millis() - pir_detection_start) / 1000);
  display.println("s");
}

void displayUltrasonicActive() {
  // Header with border
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(15, 2);
  display.println("SENSOR ULTRASONIK");
  display.drawLine(0, 14, 128, 14, SSD1306_WHITE);
  
  // Distance visualization
  int median_dist = calculateMedianDistance();
  display.setCursor(5, 20);
  display.print("Jarak: ");
  display.print(median_dist);
  display.println(" cm");
  
  // Confidence bar
  display.setCursor(5, 30);
  display.print("Confidence: ");
  display.print(detection_confidence);
  display.print("/");
  display.println(MAX_CONFIDENCE);
  
  // Visual confidence bar
  display.drawRect(5, 40, 118, 8, SSD1306_WHITE);
  int conf_width = (detection_confidence * 114) / MAX_CONFIDENCE;
  display.fillRect(7, 42, conf_width, 4, SSD1306_WHITE);
  
  // Object indicator
  display.setCursor(35, 52);
  display.println("OBJEK TERDETEKSI");
}

void displayIdleScreen() {
  // Animated header
  display.setTextSize(1);
  display.setCursor(20, 2);
  display.println("SISTEM DETEKSI");
  
  // Scanning animation
  const char* scan_states[] = {"Memindai", "Memindai.", "Memindai..", "Memindai..."};
  display.setCursor(30, 15);
  display.println(scan_states[animation_frame % 4]);
  
  // Radar visualization
  int center_x = 64;
  int center_y = 35;
  int radius = 12;
  
  // Radar circles
  display.drawCircle(center_x, center_y, radius, SSD1306_WHITE);
  display.drawCircle(center_x, center_y, radius/2, SSD1306_WHITE);
  display.drawPixel(center_x, center_y, SSD1306_WHITE);
  
  // Rotating sweep line
  float angle = (animation_frame * 20) * PI / 180;
  int end_x = center_x + radius * cos(angle);
  int end_y = center_y + radius * sin(angle);
  display.drawLine(center_x, center_y, end_x, end_y, SSD1306_WHITE);
  
  // Status line
  display.drawLine(0, 50, 128, 50, SSD1306_WHITE);
  display.setCursor(5, 53);
  display.print("PIR:OFF  US:OFF  Baseline:");
  display.print(baseline_distance);
  
  animation_frame++;
  
  // Update animation timing
  static unsigned long last_anim = 0;
  if (millis() - last_anim >= ANIMATION_DELAY) {
    last_anim = millis();
  }
}

void sendStatus() {
  Serial.print("STATUS:");
  Serial.print(pir_detected ? "1" : "0");
  Serial.print(",");
  Serial.print(ultrasonic_detected ? "1" : "0");
  Serial.print(",");
  Serial.print(calculateMedianDistance());
  Serial.print(",");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(pir_trigger_count);
  Serial.print(",");
  Serial.print(detection_confidence);
  Serial.print(",");
  Serial.print(baseline_distance);
  Serial.println();
  Serial.flush();
}

void handleSerialCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "PING") {
      Serial.println("PONG");
    } else if (command == "RESET") {
      // Reset all detection states
      pir_detected = false;
      ultrasonic_detected = false;
      pir_trigger_count = 0;
      detection_confidence = 0;
      pir_active_phase = false;
      pir_consecutive_high = 0;
      pir_consecutive_low = 0;
      animation_frame = 0;
      Serial.println("RESET_OK");
    } else if (command == "CALIBRATE") {
      startCalibration();
    } else if (command == "STATUS") {
      sendStatus();
    } else if (command.startsWith("SET_THRESHOLD:")) {
      int new_threshold = command.substring(14).toInt();
      if (new_threshold > 10 && new_threshold < 200) {
        Serial.print("THRESHOLD_SET:");
        Serial.println(new_threshold);
      } else {
        Serial.println("INVALID_THRESHOLD");
      }
    } else if (command.length() > 0) {
      Serial.print("UNKNOWN_COMMAND:");
      Serial.println(command);
    }
    Serial.flush();
  }
}