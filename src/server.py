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
        self.SIZE = 2**10
        self.PORT_TCP = 5050
        self.PORT_UDP = 5051
        self.ADDR_TCP = (socket.gethostbyname(socket.gethostname()), self.PORT_TCP)
        self.ADDR_UDP = (socket.gethostbyname(socket.gethostname()), self.PORT_UDP)
        self.HELLO = "HELLO"
        self.CONFIRM = "CONFIRM"
        self.GOODBYE = "GOODBYE"
        self.MIN_CON = min_con
        self.PATHS = ["./testFiles/100MBFile.bin","./testFiles/250MBFile.bin","./testFiles/SmallTestFile.txt"]
        self.LOCK = threading.Lock()
        
        # Logger setup
        self.logger = logger('server')
        self.logger.log_info('[STARTING] Logs initialized')

        # Server conn_tcpect
        self.server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_tcp.bind(self.ADDR_TCP)
        self.logger.log_info("[STARTING] Server is starting...")

        self.server_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_udp.bind(self.ADDR_UDP)
        self.connected=True

        # Listado de clientes
        self.clients = []
        self.fileIndex = file-1


    def start(self):
        try:
            """Función que inicaliza el servidor
            """
            # Se logea que el servidor comienza a escuchar por ADDR[0]
            self.logger.log_info("[STARTING] Server TCP is listening...")
            self.server_tcp.listen()
            self.logger.log_info(
                f"[LISTENING] Server TCP is listening on {self.ADDR_TCP[0]}")

            self.logger.log_info("[STARTING] Server UDP is listening...")
            self.logger.log_info(
                f"[LISTENING] Server UDP is listening on {self.ADDR_TCP[0]}")

            
            synchEvent = threading.Event()
            # Siempre y cuando se este escuchando
            while self.connected:
                # Acepta la conexión
                conn_tcp, addr = self.server_tcp.accept()
                self.logger.log_info(f"[CONNECTED] CONNECTION stablished with {addr}")
                self.clients.append((conn_tcp,addr))

                # Se crea un thread para manejar los clientes
                thread = threading.Thread(
                    target=self.handle_client, args=(conn_tcp,self.server_udp,addr,synchEvent))
                thread.start()
                
                #Salir del Loop
                self.conn_tcpected = self.clients == self.MIN_CON

            #Servidor se apaga
            self.logger.log_critical("[SHUTDOWN] Server is on shutdown")
        
        #Si hay algun error
        except Exception as ex:
            self.logger.log_critical(ex)
            raise ex
        
        #Cerrar
        finally:
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

    
    def handle_client(self, conn_tcp:socket, conn_udp:socket, addr:tuple, event:threading.Event):
        """Función que maneja las nuevas conexiones con el cliente

        Args:
            conn_tcp ([type]): Conexión del cliente
            addr (str): Dirección del cliente
        """
        try:
            # Logea la nueva conexión
            self.logger.log_info(f"[CONNECTION] {addr}CONNECTION")
            msg = conn_tcp.recv(self.SIZE).decode()
            if msg == self.HELLO:

                #Se envia metadata y el hash
                self.synch(event)
                fileSize = f"{self.getSyzeInMB()}"
                fileName = f"{self.PATHS[self.fileIndex].split('/')[-1]}"
                self.logger.log_info(f"[MESSAGE] File to be send is: {fileName}")
                self.logger.log_info(f"[MESSAGE] File size is of {fileSize}")
                conn_tcp.sendall(fileName.encode()+b'\n')
                conn_tcp.sendall(fileSize.encode()+b'\n')
                conn_tcp.sendall(self.PATHS[self.fileIndex].split(".")[-1].encode()+b'\n')
                conn_tcp.sendall(self.getHashFile().encode()+b'\n',)
                self.logger.log_info(f"[MESSAGE] Hash File has been sent to {addr}")
                msg = conn_tcp.recv(self.SIZE).decode()               
                
                #Se envia el archivo si llego ell hash
                if msg == self.CONFIRM:
                    self.logger.log_info(f"[MESSAGE] File transfer via UDP will begin")
                    data,address = conn_udp.recvfrom(self.SIZE)


                    with open(self.PATHS[self.fileIndex],'rb') as f:
                        init_time = time.time()
                        data = f.read(self.SIZE)
                        paquetes=1
                        while data:
                            conn_udp.sendto(data,address)
                            data = f.read(self.SIZE)
                            time.sleep(0.0001)
                            paquetes+=1
                        self.logger.log_info(f"[MESSAGE] File is has been sent to {addr} in {paquetes} packets")

                #Se envia y recibe el tiempo cuando se acaba 
                msg = conn_tcp.recv(self.SIZE).decode()
                if msg == self.CONFIRM:
                    
                    #Intercambio de tiempo
                    conn_tcp.sendall(str(init_time).encode())
                    end_time = float(conn_tcp.recv(self.SIZE).decode())
                    self.logger.log_info(f"[MESSAGE] File has been send to {addr} in {end_time-init_time} seconds")
                
                else:
                    self.logger.log_critical("Integrity check failed")
                    
            else:
                self.logger.log_error(f"[MESSAGE] Unexpected message of {addr}, bad handshake")
            
            conn_tcp.close()
            self.logger.log_info(f"[CONNECTION] {addr} connection closed")


        except Exception as ex:
            self.logger.log_critical(ex)
            raise ex




if __name__ == '__main__':
    min_con,file_name = int(sys.argv[1]),int(sys.argv[2])
    server = server(min_con,file_name)
    server.start()
