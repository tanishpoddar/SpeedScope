import customtkinter as ctk
import speedtest
import threading
from datetime import datetime
import json
import os
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class SpeedTestGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("SpeedScope - Internet Speed Analyzer")
        self.window.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize speedtest
        self.st = speedtest.Speedtest()
        self.history_file = "speed_test_history.json"
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup all GUI elements"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo and Title Frame
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(pady=20)

        # Title with custom styling
        title_label = ctk.CTkLabel(
            title_frame, 
            text="SpeedScope",
            font=("Helvetica", 32, "bold"),
            text_color="#00b4d8"  # Modern blue color
        )
        title_label.pack()

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Advanced Internet Speed Analyzer",
            font=("Helvetica", 14),
            text_color="#90e0ef"  # Lighter blue for subtitle
        )
        subtitle_label.pack(pady=5)
        
        # Speed meters frame
        self.meters_frame = ctk.CTkFrame(self.main_frame)
        self.meters_frame.pack(fill="x", padx=20, pady=10)
        
        # Download speed meter
        self.download_frame = ctk.CTkFrame(self.meters_frame)
        self.download_frame.pack(side="left", expand=True, padx=10)
        
        self.download_label = ctk.CTkLabel(
            self.download_frame,
            text="Download\n-- Mbps",
            font=("Helvetica", 16)
        )
        self.download_label.pack(pady=10)
        
        self.download_progress = ctk.CTkProgressBar(self.download_frame)
        self.download_progress.pack(pady=5)
        self.download_progress.set(0)
        
        # Upload speed meter
        self.upload_frame = ctk.CTkFrame(self.meters_frame)
        self.upload_frame.pack(side="right", expand=True, padx=10)
        
        self.upload_label = ctk.CTkLabel(
            self.upload_frame,
            text="Upload\n-- Mbps",
            font=("Helvetica", 16)
        )
        self.upload_label.pack(pady=10)
        
        self.upload_progress = ctk.CTkProgressBar(self.upload_frame)
        self.upload_progress.pack(pady=5)
        self.upload_progress.set(0)
        
        # Ping display
        self.ping_label = ctk.CTkLabel(
            self.main_frame,
            text="Ping: -- ms",
            font=("Helvetica", 16)
        )
        self.ping_label.pack(pady=10)
        
        # Start button
        self.start_button = ctk.CTkButton(
            self.main_frame,
            text="Start Test",
            command=self.start_test,
            font=("Helvetica", 14),
            height=40
        )
        self.start_button.pack(pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Ready to test",
            font=("Helvetica", 12)
        )
        self.status_label.pack(pady=5)
        
        # History graph
        self.setup_history_graph()
        
        # Credits
        credits_label = ctk.CTkLabel(
            self.main_frame,
            text="Made with ❤️ by Tanish Poddar",
            font=("Helvetica", 12),
            text_color="red"
        )
        credits_label.pack(pady=10)
        
    def setup_history_graph(self):
        """Setup the history graph frame"""
        self.graph_frame = ctk.CTkFrame(self.main_frame)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        
        # Style the graph
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white') 
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.set_title('Speed History', color='white')
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def update_graph(self):
        """Update the history graph with new data"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                
            if len(history) > 0:
                recent_history = history[-5:]  # Last 5 tests
                
                timestamps = [entry['timestamp'].split()[1] for entry in recent_history]
                downloads = [entry['download'] for entry in recent_history]
                uploads = [entry['upload'] for entry in recent_history]
                
                self.ax.clear()
                self.ax.plot(timestamps, downloads, 'g-', label='Download')
                self.ax.plot(timestamps, uploads, 'b-', label='Upload')
                
                # Style the graph
                self.ax.set_facecolor('#2b2b2b')
                self.ax.spines['bottom'].set_color('white')
                self.ax.spines['top'].set_color('white')
                self.ax.spines['right'].set_color('white')
                self.ax.spines['left'].set_color('white')
                self.ax.tick_params(axis='x', colors='white')
                self.ax.tick_params(axis='y', colors='white')
                self.ax.set_title('Speed History', color='white')
                self.ax.legend()
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45)
                
                self.fig.tight_layout()
                self.canvas.draw()
    
    def save_results(self, download, upload, ping):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "timestamp": timestamp,
            "download": round(download, 2),
            "upload": round(upload, 2),
            "ping": round(ping, 2)
        }
        
        # Load existing history or create new
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(result)
        
        # Save updated history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)
    
    def update_status(self, text):
        """Update status label"""
        self.status_label.configure(text=text)
        self.window.update_idletasks()
    
    def run_speed_test(self):
        """Run the speed test"""
        try:
            # Get best server
            self.update_status("Finding best server...")
            self.st.get_best_server()
            
            # Test download
            self.update_status("Testing download speed...")
            download_speed = self.st.download() / 1_000_000  # Convert to Mbps
            self.download_label.configure(text=f"Download\n{download_speed:.2f} Mbps")
            self.download_progress.set(min(download_speed / 100, 1))
            
            # Test upload
            self.update_status("Testing upload speed...")
            upload_speed = self.st.upload() / 1_000_000  # Convert to Mbps
            self.upload_label.configure(text=f"Upload\n{upload_speed:.2f} Mbps")
            self.upload_progress.set(min(upload_speed / 100, 1))
            
            # Get ping
            ping = self.st.results.ping
            self.ping_label.configure(text=f"Ping: {ping:.2f} ms")
            
            # Save results
            self.save_results(download_speed, upload_speed, ping)
            
            # Update graph
            self.update_graph()
            
            self.update_status("Test completed!")
            self.start_button.configure(state="normal")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.start_button.configure(state="normal")
    
    def start_test(self):
        """Start the speed test in a separate thread"""
        self.start_button.configure(state="disabled")
        self.download_progress.set(0)
        self.upload_progress.set(0)
        thread = threading.Thread(target=self.run_speed_test)
        thread.start()
    
    def run(self):
        """Start the GUI application"""
        self.window.mainloop()

if __name__ == "__main__":
    app = SpeedTestGUI()
    app.run()