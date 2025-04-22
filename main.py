import subprocess
import signal
import uuid
import tempfile
import os
import time
import shutil

YAML_CONTENT = """
apiVersion: v1
kind: Service
metadata:
  name: {service_name}
  namespace: {namespace}
spec:
  selector:
    app: {selector_label}
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}-proxy
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {selector_label}
  template:
    metadata:
      labels:
        app: {selector_label}
    spec:
      containers:
        - name: socat-proxy
          image: alpine/socat
          command: ["socat", "TCP4-LISTEN:80,fork,reuseaddr", "TCP:{host_ip}:{forward_port}"]
          ports:
            - containerPort: 80
"""


def check_and_install_socat():
    if shutil.which("socat"):
        return

    print("[info] socat not found. Attempting to install...")

    try:
        if shutil.which("apt"):
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "socat"], check=True)
        elif shutil.which("apk"):
            subprocess.run(["sudo", "apk", "add", "socat"], check=True)
        elif shutil.which("yum"):
            subprocess.run(["sudo", "yum", "install", "-y", "socat"], check=True)
        elif shutil.which("brew"):
            subprocess.run(["brew", "install", "socat"], check=True)
        else:
            raise Exception("No known package manager found to install socat.")
    except Exception as e:
        print(f"[error] Failed to install socat: {e}")
        exit(1)

    if not shutil.which("socat"):
        print("[error] socat is still not available after installation.")
        exit(1)


def run_kubectl_apply(yaml_content):
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".yaml", delete=False) as file:
        file.write(yaml_content)
        file.flush()
        print
        subprocess.run(["kubectl", "apply", "-f", file.name])
        return file.name


def run_kubectl_delete(path):
    subprocess.run(["kubectl", "delete", "-f", path])
    pass


def start_local_socat(local_port, target_port, wsl=False):
    cmd = f"socat TCP-LISTEN:{local_port},reuseaddr,fork TCP:127.0.0.1:{target_port}"
    if wsl:
        print(f"[info] Launching socat in Windows Terminal tab via wt.exe")
        subprocess.Popen([
            "wt.exe", "--window", "0", "new-tab", "--suppressApplicationTitle", "--title", f"socat-{local_port}",
            "cmd", "/k", cmd
        ])
        return None
    else:
        return subprocess.Popen(cmd.split())


def create_yaml(service_name, selector_label, host_ip, forward_port, namespace):
    return YAML_CONTENT.format(
        service_name=service_name,
        selector_label=selector_label,
        host_ip=host_ip,
        forward_port=forward_port,
        namespace=namespace
    )


def main(service_name, external_port, namespace, host_ip, wsl=False):
    if not wsl:
        check_and_install_socat()

    unique_id = str(uuid.uuid4())[:8]
    selector_label = f"{service_name}-proxy-{unique_id}"
    local_forward_port = 30000 + int(unique_id[:4], 16) % 1000

    print(f"[local] Forwarding 127.0.0.1:{local_forward_port} → 127.0.0.1:{external_port}")
    socat_proc = start_local_socat(local_forward_port, external_port, wsl=wsl)

    print(f"[k8s] Creating service `{service_name}` in namespace `{namespace}` → {host_ip}:{local_forward_port}")
    yaml_text = create_yaml(service_name, selector_label, host_ip, local_forward_port, namespace)
    yaml_path = run_kubectl_apply(yaml_text)

    def cleanup(*_):
        print("\n[cleanup] Deleting k8s resources")
        run_kubectl_delete(yaml_path)
        if socat_proc:
            socat_proc.terminate()
        os.remove(yaml_path)
        exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("[ready] Press Ctrl+C to stop")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", required=True, type=str, help="Service name")
    parser.add_argument("-p", "--port", required=True, type=int, help="Service port from Lens port forwarding")
    parser.add_argument("-H", "--host", required=True, type=str, help="Local host ip ect 192.168.1.100")
    parser.add_argument("-N", "--namespace", type=str, default="default", help="Namespace to deploy into")
    parser.add_argument("-w", "--wsl", action="store_true", help="Launch socat via wt.exe in a new terminal tab")
    args = parser.parse_args()

    main(
        service_name=args.name,
        external_port=args.port,
        namespace=args.namespace,
        host_ip=args.host,
        wsl=args.wsl
    )
