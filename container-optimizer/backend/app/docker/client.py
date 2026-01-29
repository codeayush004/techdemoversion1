import docker
import os

def get_docker_client():
    try:
        # If Docker Desktop is used, force correct socket
        if os.path.exists("/home/sigmoid/.docker/desktop/docker.sock"):
            client = docker.DockerClient(
                base_url="unix:///home/sigmoid/.docker/desktop/docker.sock"
            )
        else:
            client = docker.from_env()

        client.ping()
        return client

    except Exception as e:
        raise RuntimeError(f"Docker not accessible: {e}")
