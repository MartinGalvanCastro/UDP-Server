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
        self.SIZE = 2**10
        self.ADDR_TCP = (addr, port_tcp)
        self.ADDR_UDP = (addr, port_udp)
        self.HELLO = "HELLO"
        self.CONFIRM = "CONFIRM"
        self.GOODBYE = "GOODBYE"
        self.logger = logger("client")
        self.logger.log_info('[STARTING] Logs initialized for client')
        self.route=""


    def __call__(self):
        print("Client Status: Created")
        self.connect()     
        print("Client Status: Waiting for connections of other clients")
        self.client_tcp.sendall(self.HELLO.encode())
        
        fail=False

        #Recibe la metadata del archivo
        with self.client_tcp.makefile('rb') as serverFile:
            print("Client Status: File transfer will begin")
            fileName = serverFile.readline().strip().decode()
            fileSize = float(serverFile.readline().strip().decode())*2**20
            fileExtension = serverFile.readline().strip().decode()
            self.logger.log_info(f'[MESSAGE] File name arrived {fileName}')
            self.logger.log_info(f'[MESSAGE] File size arrived {fileSize}')
            hashFile = serverFile.readline().strip().decode()
            self.logger.log_info(f'[MESSAGE] Hash digest arrived')
            self.logger.log_info(f'[MESSAGE] File transfer will begin')
        
        #Inicializa la ruta y envia confirmación al servidor
        self.route = f'./recivedFiles/{self.name}-Prueba-{self.prueba}.{fileExtension}'
        self.client_tcp.sendall(self.CONFIRM.encode())
        self.client_udp.sendto(self.HELLO.encode(),self.ADDR_UDP)
        
        #Inicializa el pbar
        progress=0  
        pbar = tqdm(total=100,initial=progress)
        paquetes = 1



        #Escribe el archivo
        with open(self.route,'wb') as f:
            progress = 0
            prev = 0
            length = fileSize
            #Loop para recibir datos
            while length>0:
                packet = int(min(length,self.SIZE))
                data = self.client_udp.recv(packet)
                prev = int(round((fileSize-length)/fileSize*100,0))
                length-=len(data)
                progress = int(round((fileSize-length)/fileSize*100,0))
                f.write(data)
                pbar.update(progress-prev) 
                paquetes+=1
                if not data: break
        #Cierra la barra y registra el tiempo
        end_time = time.time()
        pbar.close()

        print("Client Status: Transfer complete, checking integrity")
        #Verifica que llegaron todos los datos
        if length==0:
            
            self.logger.log_info(f'[MESSAGE] File transfer complete. Checking integrity')
            localHash = self.getHashFile()

            #Se verifica el hash
            if localHash==hashFile:

                print("Integrity correct. Logging details")

                #Se confirma al servidor que es correcto el archivo
                self.client_tcp.sendall(self.CONFIRM.encode())

                #Intercambio de tiempos
                init_time = float(self.client_tcp.recv(self.SIZE).decode())
                self.client_tcp.sendall(str(end_time).encode())


                self.logger.log_critical(f'[MESSAGE] File transfer complete. Integrity correct')
                self.logger.log_critical(f'[MESSAGE] File arrived in {paquetes} packets')
                
                
                self.logger.log_info(f"[MESSAGE] File has arrived in {end_time-init_time} seconds")
            else:
                print("Integrity incorrect. Logging details")
                self.logger.log_critical(f'[MESSAGE] File transfer complete. Integrity fail')
                fail=True
        else:
            print("Integrity incorrect. Logging details")
            self.logger.log_critical(f'[MESSAGE] File transfer complete. Incorrect file')
            fail=True

        if fail:
            self.client_tcp.sendall(self.GOODBYE)
            os.remove(self.route)
            sys.exit(1)

    def connect(self):
        """Función para conectase al servidor
        """
        try:
            #Conexion al servidor
            self.client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_tcp.connect(self.ADDR_TCP)

            self.client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

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