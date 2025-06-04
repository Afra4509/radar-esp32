import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import math
import json
from datetime import datetime
import queue

class RadarDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛰️ Sistem Deteksi Radar ESP32")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a0a')
        
        # Serial communication
        self.serial_port = None
        self.is_connected = False
        self.data_queue = queue.Queue()
        self.serial_thread = None
        self.stop_thread = False
        
        # Detection states
        self.pir_active = False
        self.ultrasonic_active = False
        self.distance = 0
        self.last_update = datetime.now()
        
        # Animation variables
        self.radar_angle = 0
        self.sweep_angle = 0
        self.detection_history = []
        self.radar_blips = []
        
        # Colors
        self.colors = {
            'bg': '#0a0a0a',
            'primary': '#00ff00',
            'secondary': '#ff6600',
            'warning': '#ff0000',
            'text': '#ffffff',
            'grid': '#1a1a1a'
        }
        
        # Initialize log_text to None first
        self.log_text = None
        
        self.setup_ui()
        self.start_animation()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🛰️ SISTEM DETEKSI RADAR ESP32", 
                              font=('Arial', 20, 'bold'), 
                              fg=self.colors['primary'], bg=self.colors['bg'])
        title_label.pack(pady=(0, 20))
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Radar display
        self.setup_radar_display(content_frame)
        
        # Right side - Status and log
        self.setup_status_panel(content_frame)
        
        # Top control panel (moved after log_text is created)
        self.setup_control_panel(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        # Move to top
        control_frame.pack_configure(before=parent.winfo_children()[1])
        
        # Connection section
        conn_frame = tk.LabelFrame(control_frame, text="Koneksi Serial", 
                                  fg=self.colors['text'], bg=self.colors['bg'])
        conn_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # Port selection
        tk.Label(conn_frame, text="Port:", fg=self.colors['text'], 
                bg=self.colors['bg']).pack(side=tk.LEFT, padx=(5, 0))
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=10)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        # Now it's safe to refresh ports since log_text exists
        self.refresh_ports()
        
        # Buttons
        self.connect_btn = tk.Button(conn_frame, text="Connect", 
                                   command=self.toggle_connection,
                                   bg=self.colors['primary'], fg='black',
                                   font=('Arial', 10, 'bold'))
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(conn_frame, text="Refresh", 
                              command=self.refresh_ports,
                              bg=self.colors['secondary'], fg='black')
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        test_btn = tk.Button(conn_frame, text="Test", 
                           command=self.test_connection,
                           bg=self.colors['warning'], fg='black')
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # Status indicators
        status_frame = tk.LabelFrame(control_frame, text="Status Sistem", 
                                   fg=self.colors['text'], bg=self.colors['bg'])
        status_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        self.conn_status = tk.Label(status_frame, text="● DISCONNECTED", 
                                  fg=self.colors['warning'], bg=self.colors['bg'])
        self.conn_status.pack(side=tk.LEFT, padx=5)
        
        self.pir_status = tk.Label(status_frame, text="PIR: OFF", 
                                 fg=self.colors['text'], bg=self.colors['bg'])
        self.pir_status.pack(side=tk.LEFT, padx=5)
        
        self.ultrasonic_status = tk.Label(status_frame, text="US: OFF", 
                                        fg=self.colors['text'], bg=self.colors['bg'])
        self.ultrasonic_status.pack(side=tk.LEFT, padx=5)
        
        self.data_count = tk.Label(status_frame, text="Data: 0", 
                                 fg=self.colors['text'], bg=self.colors['bg'])
        self.data_count.pack(side=tk.LEFT, padx=5)
        
    def setup_radar_display(self, parent):
        radar_frame = tk.Frame(parent, bg=self.colors['bg'])
        radar_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Radar title
        radar_title = tk.Label(radar_frame, text="RADAR DETECTION DISPLAY", 
                             font=('Arial', 14, 'bold'), 
                             fg=self.colors['primary'], bg=self.colors['bg'])
        radar_title.pack(pady=(0, 10))
        
        # Canvas for radar
        self.radar_canvas = tk.Canvas(radar_frame, width=500, height=500, 
                                    bg=self.colors['bg'], highlightthickness=0)
        self.radar_canvas.pack(pady=10)
        
        # Detection info
        self.detection_info = tk.Label(radar_frame, text="Sistem Idle - Memindai Area", 
                                     font=('Arial', 12), 
                                     fg=self.colors['text'], bg=self.colors['bg'])
        self.detection_info.pack(pady=10)
        
    def setup_status_panel(self, parent):
        status_frame = tk.Frame(parent, bg=self.colors['bg'])
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        
        # Real-time data
        data_frame = tk.LabelFrame(status_frame, text="Data Real-Time", 
                                 fg=self.colors['text'], bg=self.colors['bg'])
        data_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.distance_label = tk.Label(data_frame, text="Jarak: -- cm", 
                                     font=('Arial', 12, 'bold'), 
                                     fg=self.colors['primary'], bg=self.colors['bg'])
        self.distance_label.pack(pady=5)
        
        self.timestamp_label = tk.Label(data_frame, text="Update: --", 
                                      fg=self.colors['text'], bg=self.colors['bg'])
        self.timestamp_label.pack(pady=5)
        
        # Raw data display
        self.raw_data_label = tk.Label(data_frame, text="Raw: --", 
                                     font=('Courier', 8), 
                                     fg=self.colors['text'], bg=self.colors['bg'])
        self.raw_data_label.pack(pady=5)
        
        # Detection log
        log_frame = tk.LabelFrame(status_frame, text="Log Deteksi", 
                                fg=self.colors['text'], bg=self.colors['bg'])
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable text widget
        self.log_text = tk.Text(log_frame, height=15, width=30, 
                              bg='#1a1a1a', fg=self.colors['text'],
                              font=('Courier', 9))
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        btn_frame = tk.Frame(log_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        clear_btn = tk.Button(btn_frame, text="Clear Log", 
                            command=self.clear_log,
                            bg=self.colors['secondary'], fg='black')
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        send_ping_btn = tk.Button(btn_frame, text="Send PING", 
                                command=self.send_ping,
                                bg=self.colors['primary'], fg='black')
        send_ping_btn.pack(side=tk.LEFT, padx=2)
        
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        # Only add log if log_text widget exists
        if self.log_text is not None:
            self.add_log(f"Found {len(ports)} ports: {', '.join(ports)}")
            
    def toggle_connection(self):
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        try:
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Error", "Pilih port serial terlebih dahulu!")
                return
                
            self.add_log(f"Mencoba koneksi ke {port}...")
            
            # Close existing connection
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.serial_port = serial.Serial(
                port=port, 
                baudrate=115200, 
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            time.sleep(2)  # Wait for ESP32 to initialize
            
            # Clear any existing data
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            
            self.is_connected = True
            self.stop_thread = False
            self.connect_btn.config(text="Disconnect", bg=self.colors['warning'])
            self.conn_status.config(text="● CONNECTED", fg=self.colors['primary'])
            
            # Start data reading thread
            self.start_data_thread()
            self.add_log(f"Koneksi berhasil ke {port}")
            
            # Send initial ping
            self.root.after(1000, self.send_ping)
                
        except Exception as e:
            self.add_log(f"Gagal terhubung: {str(e)}")
            messagebox.showerror("Connection Error", f"Gagal terhubung: {str(e)}")
            if self.serial_port:
                try:
                    self.serial_port.close()
                except:
                    pass
                self.serial_port = None
                
    def disconnect_serial(self):
        self.is_connected = False
        self.stop_thread = True
        
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
            
        self.connect_btn.config(text="Connect", bg=self.colors['primary'])
        self.conn_status.config(text="● DISCONNECTED", fg=self.colors['warning'])
        self.add_log("Koneksi terputus")
        
    def start_data_thread(self):
        def read_data():
            data_counter = 0
            while self.is_connected and not self.stop_thread and self.serial_port:
                try:
                    if self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        if line:
                            data_counter += 1
                            self.root.after_idle(lambda: self.data_count.config(text=f"Data: {data_counter}"))
                            self.root.after_idle(lambda l=line: self.raw_data_label.config(text=f"Raw: {l[:20]}..."))
                            
                            # Process different types of messages
                            if line.startswith("STATUS:"):
                                self.process_status_data(line)
                            elif line == "PONG":
                                self.add_log("PING response: PONG")
                            elif line == "SYSTEM_READY":
                                self.add_log("ESP32 system ready!")
                            else:
                                self.add_log(f"ESP32: {line}")
                    else:
                        time.sleep(0.01)  # Small delay when no data
                        
                except Exception as e:
                    if self.is_connected and not self.stop_thread:
                        self.add_log(f"Error reading data: {e}")
                        break
                        
            self.add_log("Data thread stopped")
                    
        self.serial_thread = threading.Thread(target=read_data, daemon=True)
        self.serial_thread.start()
        
    def process_status_data(self, line):
        try:
            # Parse STATUS:pir,ultrasonic,distance,timestamp
            data_part = line.replace("STATUS:", "")
            data = data_part.split(",")
            
            if len(data) >= 4:
                prev_pir = self.pir_active
                prev_ultrasonic = self.ultrasonic_active
                
                self.pir_active = data[0] == '1'
                self.ultrasonic_active = data[1] == '1'
                self.distance = int(data[2]) if data[2].isdigit() else 0
                self.last_update = datetime.now()
                
                # Update UI in main thread
                self.root.after_idle(self.update_status_display)
                
                # Log changes
                if prev_pir != self.pir_active or prev_ultrasonic != self.ultrasonic_active:
                    self.root.after_idle(self.log_detection_change)
                    
                # Add radar blip if detected
                if self.pir_active or self.ultrasonic_active:
                    self.root.after_idle(self.add_radar_blip)
                    
        except Exception as e:
            self.add_log(f"Error parsing data: {e}")
            
    def test_connection(self):
        if self.is_connected and self.serial_port:
            self.send_ping()
        else:
            self.add_log("Not connected - cannot test")
            
    def send_ping(self):
        if self.is_connected and self.serial_port:
            try:
                self.serial_port.write(b"PING\n")
                self.serial_port.flush()
                self.add_log("Sent PING command")
            except Exception as e:
                self.add_log(f"Error sending PING: {e}")
                
    def update_status_display(self):
        # Update status labels
        pir_color = self.colors['primary'] if self.pir_active else self.colors['text']
        us_color = self.colors['primary'] if self.ultrasonic_active else self.colors['text']
        
        self.pir_status.config(text=f"PIR: {'ON' if self.pir_active else 'OFF'}", fg=pir_color)
        self.ultrasonic_status.config(text=f"US: {'ON' if self.ultrasonic_active else 'OFF'}", fg=us_color)
        
        # Update distance
        if self.distance < 200 and self.distance > 0:
            self.distance_label.config(text=f"Jarak: {self.distance} cm")
        else:
            self.distance_label.config(text="Jarak: -- cm")
            
        # Update timestamp
        self.timestamp_label.config(text=f"Update: {self.last_update.strftime('%H:%M:%S')}")
        
        # Update detection info
        if self.pir_active and self.ultrasonic_active:
            self.detection_info.config(text="🚨 DETEKSI MAKSIMAL - KEDUA SENSOR AKTIF!", 
                                     fg=self.colors['warning'])
        elif self.pir_active:
            self.detection_info.config(text="🔴 SENSOR PIR AKTIF - Gerakan Terdeteksi", 
                                     fg=self.colors['primary'])
        elif self.ultrasonic_active:
            self.detection_info.config(text="🔵 SENSOR ULTRASONIK AKTIF - Objek Terdeteksi", 
                                     fg=self.colors['secondary'])
        else:
            self.detection_info.config(text="🔍 Sistem Idle - Memindai Area", 
                                     fg=self.colors['text'])
                                     
    def log_detection_change(self):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.pir_active and self.ultrasonic_active:
            status = "KEDUA SENSOR AKTIF"
        elif self.pir_active:
            status = "PIR AKTIF"
        elif self.ultrasonic_active:
            status = "ULTRASONIK AKTIF"
        else:
            status = "SEMUA SENSOR OFF"
            
        self.add_log(f"[{timestamp}] {status}")
        
    def add_radar_blip(self):
        # Add detection blip to radar
        angle = self.radar_angle
        distance_ratio = min(self.distance / 100.0, 1.0) if self.distance < 200 and self.distance > 0 else 0.8
        
        blip = {
            'angle': angle,
            'distance': distance_ratio,
            'pir': self.pir_active,
            'ultrasonic': self.ultrasonic_active,
            'timestamp': time.time(),
            'fade': 1.0
        }
        
        self.radar_blips.append(blip)
        
        # Keep only recent blips
        current_time = time.time()
        self.radar_blips = [b for b in self.radar_blips if (current_time - b['timestamp']) < 5]
        
    def add_log(self, message):
        def update_log():
            # Check if log_text widget exists and is valid
            if self.log_text is not None:
                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                    self.log_text.see(tk.END)
                except tk.TclError:
                    # Widget has been destroyed
                    pass
            
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after_idle(update_log)
            
    def clear_log(self):
        if self.log_text is not None:
            self.log_text.delete(1.0, tk.END)
        
    def draw_radar(self):
        try:
            canvas = self.radar_canvas
            canvas.delete("all")
            
            # Canvas dimensions
            width = 500
            height = 500
            center_x = width // 2
            center_y = height // 2
            max_radius = min(width, height) // 2 - 20
            
            # Draw radar circles
            for i in range(1, 5):
                radius = (max_radius * i) // 4
                canvas.create_oval(center_x - radius, center_y - radius,
                                 center_x + radius, center_y + radius,
                                 outline=self.colors['grid'], width=1)
                                 
            # Draw radar lines
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                end_x = center_x + max_radius * math.cos(rad)
                end_y = center_y + max_radius * math.sin(rad)
                canvas.create_line(center_x, center_y, end_x, end_y,
                                 fill=self.colors['grid'], width=1)
                                 
            # Draw sweep line
            sweep_rad = math.radians(self.sweep_angle)
            sweep_end_x = center_x + max_radius * math.cos(sweep_rad)
            sweep_end_y = center_y + max_radius * math.sin(sweep_rad)
            canvas.create_line(center_x, center_y, sweep_end_x, sweep_end_y,
                             fill=self.colors['primary'], width=2)
                             
            # Draw detection blips
            for blip in self.radar_blips:
                blip_radius = max_radius * blip['distance']
                blip_rad = math.radians(blip['angle'])
                blip_x = center_x + blip_radius * math.cos(blip_rad)
                blip_y = center_y + blip_radius * math.sin(blip_rad)
                
                # Fade out over time
                fade = max(0, 1.0 - (time.time() - blip['timestamp']) / 5.0)
                
                # Color based on sensor type
                if blip['pir'] and blip['ultrasonic']:
                    color = self.colors['warning']
                    size = 8
                elif blip['pir']:
                    color = self.colors['primary']
                    size = 6
                elif blip['ultrasonic']:
                    color = self.colors['secondary']
                    size = 6
                else:
                    color = self.colors['text']
                    size = 4
                    
                # Draw blip with fade effect
                if fade > 0:
                    canvas.create_oval(blip_x - size, blip_y - size,
                                     blip_x + size, blip_y + size,
                                     fill=color, outline=color)
                                     
            # Draw center point
            canvas.create_oval(center_x - 3, center_y - 3,
                             center_x + 3, center_y + 3,
                             fill=self.colors['primary'], outline=self.colors['primary'])
                             
            # Draw labels
            canvas.create_text(center_x, 20, text="0°", fill=self.colors['text'])
            canvas.create_text(center_x, height - 20, text="180°", fill=self.colors['text'])
            canvas.create_text(20, center_y, text="270°", fill=self.colors['text'])
            canvas.create_text(width - 20, center_y, text="90°", fill=self.colors['text'])
            
            # Connection status indicator
            if self.is_connected:
                canvas.create_text(50, height - 30, text="● ONLINE", fill=self.colors['primary'])
            else:
                canvas.create_text(50, height - 30, text="● OFFLINE", fill=self.colors['warning'])
        except tk.TclError:
            # Canvas has been destroyed, stop drawing
            pass
        
    def start_animation(self):
        def animate():
            while True:
                try:
                    # Update sweep angle
                    self.sweep_angle = (self.sweep_angle + 2) % 360
                    self.radar_angle = (self.radar_angle + 1) % 360
                    
                    # Update radar display
                    self.root.after_idle(self.draw_radar)
                    
                    time.sleep(0.05)  # 20 FPS
                except:
                    break
                
        thread = threading.Thread(target=animate, daemon=True)
        thread.start()

def main():
    root = tk.Tk()
    app = RadarDetectionGUI(root)
    
    def on_closing():
        if app.is_connected:
            app.disconnect_serial()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()