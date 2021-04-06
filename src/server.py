import socket
import threading
import sys
import os
import hashlib
import math
import time
from logger import logger


class server():
    """Clase servidor TCP
    """

    def __init__(self, min_env: int, file: int):
        """Función para crear un servidor
        Args:
            min_env (int): Minimo numero de conexiones para enviar el archivo
            file (int): Archivo a seleccionar:
                        1. Arhcivo 100MB
                        2. Archivo 200MB
        """

        # Server asserts
        assert 1 <= min_con <= 25, "El numero maximo de conexiones son 25"
        assert 1 <= file <= 3, "El archivo no es el indicado"

        # Server class constant
        self.HEADER = 2**20
        self.PORT = 5050
        self.ADDR = (socket.gethostbyname(socket.gethostname()), self.PORT)
        self.HELLO = "HELLO"
        self.CONFIRM = "CONFIRM"
        self.GOODBYE = "GOODBYE"
        self.MIN_CON = min_con
        self.PATHS = ["./testFiles/100MBFile.bin","./testFiles/250MBFile.bin","./testFiles/SmallTestFile.txt"]
        self.LOCK = threading.Lock()
        
        # Logger setup
        self.logger = logger('server')
        self.logger.log_info('[STARTING] Logs initialized')

        # Server connect
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)
        self.logger.log_info("[STARTING] Server is starting...")
        self.connected=True

        # Listado de clientes
        self.clients = []
        self.fileIndex = file-1


    def start(self):
        try:
            """Función que inicaliza el servidor
            """
            # Se logea que el servidor comienza a escuchar por ADDR[0]
            self.logger.log_info("[STARTING] Server is listening...")
            self.server.listen()
            self.logger.log_info(
                f"[LISTENING] Server is listening on {self.ADDR[0]}")
            synchEvent = threading.Event()
            # Siempre y cuando se este escuchando
            while self.connected:
                # Acepta la conexión
                conn, addr = self.server.accept()
                self.logger.log_info(f"[CONNECTED] Connection stablished with {addr}")
                self.clients.append((conn,addr))

                # Se crea un thread para manejar los clientes
                thread = threading.Thread(
                    target=self.handle_client, args=(conn,addr,synchEvent))
                thread.start()
                # Se logea la nueva conexión
            self.logger.log_critical("[SHUTDOWN] Server is on shutdown")
        except Exception as ex:
            self.logger.log_critical(ex)
            raise ex
            sys.exit(1)
        

    def synch(self,event:threading.Event):
        """Metodo para sincronizar los clientes con un semaforo
        """
        aux = True
        with self.LOCK:
            self.logger.log_info(f"[CONNECTION] {len(self.clients)} Clients ready")
            if len(self.clients)==self.MIN_CON:
                event.set()
                aux=False
        if aux:
            event.wait()

    def getSyzeInMB(self)->float:
        """Función para obtener tamaño del archivo en MB
        Args:
            path (str): Path al archivo

        Returns:
            int: Tamaño en MB
        """
        return os.path.getsize(self.PATHS[self.fileIndex])/2**20
    
    def getHashFile(self):
        h = hashlib.sha1()
        with open(self.PATHS[self.fileIndex],'rb') as file:
            chunk = file.read()
            h.update(chunk)
        return h.hexdigest()

    
    def handle_client(self, conn:socket, addr:tuple,event:threading.Event):
        """Función que maneja las nuevas conexiones con el cliente

        Args:
            conn ([type]): Conexión del cliente
            addr (str): Dirección del cliente
        """
        try:
            # Logea la nueva conexión
            self.logger.log_info(f"[NEW CONNECTION] {addr} connected")
            msg = conn.recv(self.HEADER).decode()
            if msg == self.HELLO:
                self.synch(event)
                with open(self.PATHS[self.fileIndex],'rb') as f:
                    fileSize = f"{self.getSyzeInMB()}"
                    fileName = f"{self.PATHS[self.fileIndex].split('/')[-1]}"
                    self.logger.log_info(f"[MESSAGE] File to be send is: {fileName}")
                    self.logger.log_info(f"[MESSAGE] File size is of {fileSize}")
                    conn.sendall(fileName.encode()+b'\n')
                    conn.sendall(fileSize.encode()+b'\n')
                    conn.sendall(self.PATHS[self.fileIndex].split(".")[-1].encode()+b'\n')
                    conn.sendall(self.getHashFile().encode()+b'\n',)
                    self.logger.log_info(f"[MESSAGE] Hash File has been sent to {addr}")
                    init_time = time.time()
                    data = f.read(self.HEADER)
                    self.logger.log_info(f"[MESSAGE] File is been send to {addr}")
                    paquetes=1
                    while data:
                        conn.sendall(data)
                        data = f.read(self.HEADER)
                        paquetes+=1
                    self.logger.log_info(f"[MESSAGE] File is has been sent to {addr} in {paquetes} packets")
                msgRcv = conn.recv(self.HEADER).decode()
                if msgRcv and msgRcv==self.CONFIRM:
                    conn.sendall(str(init_time).encode())
                    end_time = float(conn.recv(self.HEADER).decode())
                    self.logger.log_info(f"[MESSAGE] File has been send to {addr} in {end_time-init_time} seconds")
                else:
                    self.logger.log_error(f"[MESSAGE] Error while sending file to {addr}")

            else:
                self.logger.log_error(f"[MESSAGE] Unexpected message of {addr}, bad handshake")
            
            conn.close()
            self.logger.log_info(f"[CONNECTION] {addr} connection closed")

        except Exception as ex:
            self.logger.log_critical(ex)
            raise ex
            sys.exit(1)




if __name__ == '__main__':
    min_con,file_name = int(sys.argv[1]),int(sys.argv[2])
    serverTCP = server(min_con,file_name)
    serverTCP.start()
