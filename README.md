# 🛰️ ESP32 Radar Detection System

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![ESP32](https://img.shields.io/badge/ESP32-Compatible-green.svg)](https://espressif.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()


---

## 🌟 Fitur Unggulan

### 🔥 **Real-Time Detection**
- **Sensor PIR** - Deteksi gerakan dengan akurasi tinggi
- **Sensor Ultrasonik SF05** - Pengukuran jarak presisi (≤ 50 cm)
- **Dual Detection Mode** - Kombinasi kedua sensor untuk akurasi maksimal

### 📺 **OLED Display**
- Status sensor real-time
- Animasi idle yang menarik
- Indikator deteksi visual
- Mode hemat daya

### 🛰️ **GUI Radar Python**
- **Visualisasi radar 360°** dengan animasi smooth
- **Real-time data streaming** via Serial
- **Detection logging** dengan timestamp
- **Status monitoring** sistem
- **Dark theme** dengan UI modern
- **Radar sweep animation** saat idle

---

## 🚀 Quick Start

### 📋 Prerequisites

```bash
# Hardware Requirements
✅ ESP32 Development Board
✅ PIR Motion Sensor
✅ Ultrasonic Sensor SF05
✅ OLED Display 0.96" I2C
✅ Breadboard & Jumper Wires
✅ USB Cable

# Software Requirements
✅ Arduino IDE 1.8.19+
✅ Python 3.7+
✅ pip package manager
```

### ⚡ Installation

#### 1. **Clone Repository**
```bash
git clone https://github.com/Afra4509/radar-esp32.git
cd radar-esp32
```

#### 2. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

#### 3. **Arduino Libraries**
Install the following libraries through Arduino IDE Library Manager:
```
• Adafruit_SSD1306
• Adafruit_GFX_Library
• Wire (built-in)
• NewPing or similar ultrasonic library
```

---

## 🔌 Hardware Wiring

### 📐 **Connection Diagram**

| **Component** | **ESP32 Pin** | **Description** |
|---------------|---------------|-----------------|
| **OLED SDA** | GPIO 21 | I2C Data Line |
| **OLED SCL** | GPIO 22 | I2C Clock Line |
| **PIR Signal** | GPIO 33 | Motion Detection |
| **SF05 Trigger** | GPIO 13 | Ultrasonic Trigger |
| **SF05 Echo** | GPIO 12 | Ultrasonic Echo |
| **VCC** | 3.3V/5V | Power Supply |
| **GND** | GND | Ground |

### 🔧 **Wiring Schematic**
```
ESP32                    Components
┌─────────────┐         ┌──────────┐
│   GPIO 21   ├─────────┤ OLED SDA │
│   GPIO 22   ├─────────┤ OLED SCL │
│   GPIO 33   ├─────────┤ PIR OUT  │
│   GPIO 13   ├─────────┤ SF05 TRIG│
│   GPIO 12   ├─────────┤ SF05 ECHO│
│     3.3V    ├─────────┤   VCC    │
│     GND     ├─────────┤   GND    │
└─────────────┘         └──────────┘
```

---

## 💻 Software Setup

### 🔧 **ESP32 Programming**

1. **Open Arduino IDE**
2. **Select Board**: ESP32 Dev Module
3. **Set Port**: Your ESP32 COM port
4. **Upload** the ESP32 code from `/ESP32_code/radar_detection.ino`

### 🐍 **Python GUI Setup**

1. **Navigate to project directory**
```bash
cd radar-esp32
```

2. **Run the GUI application**
```bash
python radar_gui.py
```

3. **Connect to ESP32**
   - Select correct COM port
   - Click "Connect"
   - System will auto-detect and start monitoring

---

## 🎯 Usage Guide

### 🖥️ **GUI Interface**

#### **Control Panel**
- **Port Selection**: Choose ESP32 COM port
- **Connect/Disconnect**: Manage serial connection
- **Refresh**: Update available ports
- **Test**: Send ping command to ESP32

#### **Status Indicators**
- 🟢 **Connected**: System online
- 🔴 **PIR Status**: Motion sensor state
- 🔵 **Ultrasonic Status**: Distance sensor state
- 📊 **Data Counter**: Real-time packet count

#### **Radar Display**
- **360° Sweep Animation**: Continuous radar scanning
- **Detection Blips**: Visual representation of detections
- **Color Coding**:
  - 🟢 Green: PIR detection
  - 🟠 Orange: Ultrasonic detection  
  - 🔴 Red: Dual sensor detection

#### **Detection Log**
- Real-time event logging
- Timestamp for each detection
- Clear log functionality
- Auto-scroll to latest entry

---

## 📊 System Behavior

### 🎭 **Detection Modes**

| **Mode** | **PIR** | **Ultrasonic** | **Display** | **GUI Color** |
|----------|---------|----------------|-------------|---------------|
| **Idle** | OFF | OFF | "Sedang memindai..." | White |
| **Motion** | ON | OFF | "Sensor 1 mendeteksi" | Green |
| **Distance** | OFF | ON | "Sensor 2 mendeteksi" | Orange |
| **Maximum** | ON | ON | "Kedua sensor aktif!" | Red |

### 📡 **Communication Protocol**

#### **ESP32 → Python**
```
STATUS:pir,ultrasonic,distance,timestamp
Example: STATUS:1,0,25,1640995200
```

#### **Python → ESP32**
```
PING          → Test connection
SYSTEM_READY  → Initialization complete
```

---

## 🛠️ Troubleshooting

### ❌ **Common Issues**

#### **Connection Problems**
```bash
# Issue: Cannot connect to ESP32
✅ Check COM port selection
✅ Verify ESP32 is powered on
✅ Try different USB cable
✅ Restart Arduino IDE and Python script
```

#### **Sensor Not Working**
```bash
# Issue: No sensor readings
✅ Check wiring connections
✅ Verify power supply (3.3V/5V)
✅ Test individual sensors
✅ Check GPIO pin assignments
```

#### **GUI Issues**
```bash
# Issue: GUI not responding
✅ Update Python to 3.7+
✅ Reinstall requirements: pip install -r requirements.txt
✅ Check serial port permissions
✅ Close other serial monitor applications
```

---

## 🔧 Customization

### ⚙️ **ESP32 Configuration**
```cpp
// Sensor pins (ESP32_code/config.h)
#define PIR_PIN 33
#define TRIG_PIN 13
#define ECHO_PIN 12
#define OLED_SDA 21
#define OLED_SCL 22

// Detection thresholds
#define ULTRASONIC_THRESHOLD 50  // cm
#define PIR_DELAY 2000          // ms
```

### 🎨 **GUI Customization**
```python
# Color scheme (radar_gui.py)
self.colors = {
    'bg': '#0a0a0a',        # Background
    'primary': '#00ff00',    # Primary accent
    'secondary': '#ff6600',  # Secondary accent
    'warning': '#ff0000',    # Alert color
    'text': '#ffffff',       # Text color
    'grid': '#1a1a1a'       # Grid lines
}
```

---

## 📈 Performance Specs

| **Metric** | **Value** |
|------------|-----------|
| **Scan Rate** | 20 FPS |
| **Detection Range** | 0-50 cm (Ultrasonic) |
| **PIR Angle** | 120° |
| **Response Time** | <100ms |
| **Serial Baudrate** | 115200 |
| **Power Consumption** | ~200mA |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### 📝 **Contribution Areas**
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🔧 Performance optimizations

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Afra4509**
- 🌐 GitHub: [@Afra4509](https://github.com/Afra4509)
- 📧 Email: [Contact via GitHub](https://github.com/Afra4509)
- 🚀 Repository: [radar-esp32](https://github.com/Afra4509/radar-esp32)

---

## 🙏 Acknowledgments

- **Espressif** for the amazing ESP32 platform
- **Adafruit** for excellent OLED libraries
- **Python Community** for tkinter and serial libraries
- **Open Source Community** for inspiration and support

---

## 🚀 Future Enhancements

- [ ] **Web Interface** - Browser-based monitoring
- [ ] **WiFi Connectivity** - Wireless data transmission
- [ ] **Data Logging** - SQLite database storage
- [ ] **Multi-sensor Support** - Expandable sensor array
- [ ] **Mobile App** - Android/iOS companion app
- [ ] **Machine Learning** - Pattern recognition
- [ ] **Alert System** - Email/SMS notifications

---

<div align="center">

### 🌟 **Star this repository if you found it helpful!** 🌟

![Star Badge](https://img.shields.io/github/stars/Afra4509/radar-esp32?style=social)
![Fork Badge](https://img.shields.io/github/forks/Afra4509/radar-esp32?style=social)
![Watch Badge](https://img.shields.io/github/watchers/Afra4509/radar-esp32?style=social)


</div>
