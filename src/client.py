import socket
import os
import sys  
import hashlib
import time
from tqdm import tqdm
from logger import logger


class client():

    def __init__(self, id: int, prueba: int, addr: str, port_tcp: int, port_udp:int):
        """Función que crea un cliente
        Args:
            id (int): Id del cliente
            prueba (int): Numero de Prueba a practicar
            addr (str): Dirección IP del servidor
            port (int): Puerto del servidor
        """
        self.name = f"Cliente{id}"
        self.prueba = prueba
        self.SIZE = 2**16
        self.ADDR_TCP = (addr, port_tcp)
        self.ADDR_UDP = (addr, port_udp)
        self.HELLO = "HELLO"
        self.CONFIRM = "CONFIRM"
        self.GOODBYE = "GOODBYE"
        self.logger = logger("client")
        self.logger.log_info('[STARTING] Logs initialized for client')
        self.route=""


    def __call__(self):
        self.connect()
        progress=0       
        pbar = tqdm(total=100,initial=progress)
        print("")

        self.client_tcp.sendall(self.HELLO.encode())
        fail=False
        with self.client_tcp.makefile('rb') as serverFile:
            fileName = serverFile.readline().strip().decode()
            fileSize = float(serverFile.readline().strip().decode())*2**20
            fileExtension = serverFile.readline().strip().decode()
            self.logger.log_info(f'[MESSAGE] File name arrived {fileName}')
            self.logger.log_info(f'[MESSAGE] File size arrived {fileSize}')
            hashFile = serverFile.readline().strip().decode()
            self.logger.log_info(f'[MESSAGE] Hash digest arrived')
            self.logger.log_info(f'[MESSAGE] File transfer will begin')
        self.route = f'./recivedFiles/{self.name}-Prueba-{self.prueba}.{fileExtension}'
        self.client_tcp.sendall(self.CONFIRM.encode())

        
        paquetes = 1
        with open(self.route,'wb') as f:
            progress = 0
            length = fileSize
            while length>0:
                print("length")
                packet = int(min(fileSize,self.SIZE))
                data = self.client_udp.recvfrom(packet)
                print(data[0])
                length-=len(data[0])
                progress = int(round((fileSize-length)/fileSize*100,0))
                f.write(data[0])
                pbar.update(progress)
                paquetes+=1
                if not data: break
        pbar.close()
        print("Acabo")
    def connect(self):
        """Función para conectase al servidor
        """
        try:
            #Conexion al servidor
            self.client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_tcp.connect(self.ADDR_TCP)

            self.client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_udp.bind(self.ADDR_UDP)

        except Exception as ex:
            self.logger.log_critical(ex)
            raise ex
    

    def getHashFile(self):
        h = hashlib.sha1()
        with open(self.route,'rb') as file:
            chunk = 0
            while chunk != b'':
                chunk = file.read(1024)
                h.update(chunk)
        return h.hexdigest()

            
if __name__ == '__main__':
    id = int(sys.argv[1])
    direccion = socket.gethostbyname(socket.gethostname())
    puerto_tcp =5050
    puerto_udp = 5051
    nuevoCliente = client(id,1,direccion,puerto_tcp,puerto_udp)
    nuevoCliente()