import docker
import os

def get_docker_client():
    try:
        # If Docker Desktop is used, force correct socket
        # Try standard environment variable first
        socket_path = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        
        # Fallback to local user desktop socket if it exists (generalized)
        user_socket = os.path.expanduser("~/.docker/desktop/docker.sock")
        if os.path.exists(user_socket):
            client = docker.DockerClient(base_url=f"unix://{user_socket}")
        else:
            client = docker.from_env()

        client.ping()
        return client

    except Exception as e:
        raise RuntimeError(f"Docker not accessible: {e}")
