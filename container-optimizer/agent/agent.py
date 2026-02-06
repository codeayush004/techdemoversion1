import docker
import requests
import argparse
import sys
import json
import time

def scan_local_containers(sync_code, api_base_url):
    print(f"🚀 Initializing Local Agent (Sync Code: {sync_code})")
    print(f"🔗 Connecting to Azure Control Hub at: {api_base_url}")
    
    try:
        client = docker.from_env()
        containers = client.containers.list()
        
        if not containers:
            print("⚠️ No running containers found on this host.")
            return

        print(f"📡 Found {len(containers)} running containers. Extracting metadata...")
        
        container_data = []
        for container in containers:
            try:
                # Deep inspect
                details = container.attrs
                
                # Extract critical info for AI analysis
                payload = {
                    "id": container.id,
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else details['Config']['Image'],
                    "status": container.status,
                    "config": {
                        "Env": details['Config'].get('Env', []),
                        "User": details['Config'].get('User', ''),
                        "ExposedPorts": details['Config'].get('ExposedPorts', {}),
                        "Volumes": details['Config'].get('Volumes', {}),
                    },
                    "host_config": {
                        "Privileged": details['HostConfig'].get('Privileged', False),
                        "Memory": details['HostConfig'].get('Memory', 0),
                        "CpuPercent": details['HostConfig'].get('CpuPercent', 0),
                    }
                }
                container_data.append(payload)
                print(f"   ✅ Collected info for: {container.name}")
            except Exception as e:
                print(f"   ❌ Error inspecting {container.name}: {str(e)}")

        # System info
        system_info = {
            "platform": sys.platform,
            "docker_version": client.version().get('Version', 'unknown')
        }

        # Sync to Azure
        sync_url = f"{api_base_url}/agent/sync/{sync_code}"
        response = requests.post(
            sync_url, 
            json={
                "containers": container_data,
                "system_info": system_info
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("\n✨ SUCCESS! Local containers synchronized to Azure.")
            print("💎 You can now view and optimize them on your browser dashboard.")
        else:
            print(f"\n❌ Sync failed: {response.text}")

    except Exception as e:
        print(f"\n❌ Agent Error: {str(e)}")
        if "Permission denied" in str(e):
            print("💡 Tip: Try running with 'sudo' or check your docker group permissions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Local Agent")
    parser.add_argument("--code", required=True, help="The 6-character sync code from your Azure dashboard")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api", help="The API base URL (default: localhost for testing)")
    
    args = parser.parse_args()
    
    scan_local_containers(args.code, args.url)
