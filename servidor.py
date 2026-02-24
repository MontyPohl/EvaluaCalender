import socket
import threading


clientes = []


def broadcast(mensaje, remitente):

    for cliente in clientes:
        if cliente != remitente:
            try:
                cliente.send(mensaje)
            except:
                if cliente in clientes:
                    clientes.remove(cliente)


def manejar_clientes(conn, addr):

    print(f"[HILO] manejando cliente {addr}")
    try:
        nombre = conn.recv(1024).decode("utf-8")
    except:
        nombre = "Usuario desconocido"

    # Notificar a todos
    mensaje_conexion = f"[SISTEMA] se ha unido al chat \n{nombre}".encode("utf-8")

    broadcast(mensaje_conexion, conn)
    while True:
        try:
            mensaje = conn.recv(1024)
            if not mensaje:
                break

            print(f'Mensaje de {addr}: {mensaje.decode("utf-8")}')

            broadcast(mensaje, conn)
            print(f"Cliente {addr} conectado")
        except:
            break

    print(f"Cliente {addr} desconectado")
    if conn in clientes:
        clientes.remove(conn)
    conn.close()


# SOL_SOCKET  es como si fuera una libreria donde esta SO_REUSEADDR
# el uno simboliza el True
# SOCK_STREAM protocolo de envio de datos
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("localhost", 9999))
server_socket.listen(5)

server_socket.settimeout(1)

print("Servidor esperando conexion")

try:

    while True:
        try:
            conn, addr = server_socket.accept()
            clientes.append(conn)

            print(f"Nuevo cliente: {addr}. Total: {len(clientes)}")
            # iniciar hilo para recibir

            hilo = threading.Thread(target=manejar_clientes, args=(conn, addr))
            hilo.daemon = True
            hilo.start()
        except socket.timeout:
            continue


except KeyboardInterrupt:
    print("\nCerrando servidor")
    for cliente in clientes:
        try:
            cliente.close()
        except:
            pass
    server_socket.close()
    print("servidor cerrado")
