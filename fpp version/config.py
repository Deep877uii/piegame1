import os

# Default configuration
DEFAULT_CONFIG = {
    'PORT': 5000,
    'PORT_RANGE': (5000, 6000),  # Range of ports to try if default port is in use
    'HOST': '0.0.0.0'
}

def get_config():
    """Get configuration from environment variables or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # Try to get port from environment variable
    env_port = os.getenv('APP_PORT')
    if env_port:
        try:
            config['PORT'] = int(env_port)
        except ValueError:
            print(f"Warning: Invalid port number in environment variable APP_PORT: {env_port}")
    
    return config

def find_available_port(start_port, end_port):
    """Find an available port in the given range"""
    import socket
    
    for port in range(start_port, end_port + 1):
        try:
            # Try to create a socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    return None 