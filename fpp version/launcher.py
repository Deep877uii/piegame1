import tkinter as tk
from tkinter import ttk
import webbrowser
import threading
import web_app
from config import get_config, find_available_port
import sys
import socket
import time

class GameLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Launcher")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 12))
        style.configure('TLabel', font=('Arial', 12))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Game Launcher", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Click Start to launch the game")
        self.status_label.pack(pady=10)
        
        # Port label
        self.port_label = ttk.Label(main_frame, text="Port: Not started")
        self.port_label.pack(pady=5)
        
        # Link label
        self.link_label = ttk.Label(main_frame, text="", foreground="blue", cursor="hand2")
        self.link_label.pack(pady=5)
        self.link_label.bind("<Button-1>", self.open_browser)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # Start button
        self.start_button = ttk.Button(button_frame, text="Start Game", command=self.start_game)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(button_frame, text="Stop Game", command=self.stop_game, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.server_thread = None
        self.running = False
        self.current_port = None
        
    def start_game(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Starting game server...")
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
    def stop_game(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Game server stopped")
        self.port_label.config(text="Port: Not started")
        self.link_label.config(text="")
        
    def is_port_available(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(('localhost', port)) != 0
        
    def run_server(self):
        config = get_config()
        port = config['PORT']
        
        # Check if port is available
        if not self.is_port_available(port):
            port = find_available_port(*config['PORT_RANGE'])
            if not port:
                self.update_status("Error: Could not find available port")
                self.stop_game()
                return
        
        self.current_port = port
        self.running = True
        
        self.update_status(f"Server running on port {port}")
        self.update_link(port)
        
        # Open browser automatically
        webbrowser.open(f"http://localhost:{port}")
        
        # Run the Flask app
        web_app.app.run(host=config['HOST'], port=port, debug=False, use_reloader=False)
                
    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))
        
    def update_link(self, port):
        url = f"http://localhost:{port}"
        self.root.after(0, lambda: self.port_label.config(text=f"Port: {port}"))
        self.root.after(0, lambda: self.link_label.config(text=f"Click to open: {url}"))
        
    def open_browser(self, event):
        if self.current_port:
            webbrowser.open(f"http://localhost:{self.current_port}")
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
