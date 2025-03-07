import os
import shutil
from ftplib import FTP

from django.core.files import File

from home.models import Maps


class UpdateDBmaps():
    def __init__(self, filesnames: list, type: str) -> None:
        self.__filesnames = filesnames
        self.__type = type
        self.__path='Salida/Mapas/'
        self.__model = Maps

    def dowload(self):
        try:
            ftp = FTP(host='10.0.100.204')
            ftp.encoding = 'utf-8'
            ftp.login(user='todos', passwd='todos')

            for filename in self.__filesnames:
                with open(f"{self.__path}{filename}", "wb") as file:
                    ftp.retrbinary(f"RETR {self.__path}{filename}", file.write)

            ftp.quit()
        except Exception as e:
            print(f'Error: {e}')

    def update(self):
        self.dowload()
        files = self.__filesnames
        for i in range(len(files)):
            hour = files[i].split('.')[0][-2:]
            type = self.__type
            image_path = f'{self.__path}{files[i]}'
            
            # Verificar que el archivo existe
            if os.path.isfile(image_path):
                # Abrir la imagen
                with open(image_path, 'rb') as img_file:
                    image = File(img_file)

                    # Verificar que este en la db
                    object = self.__model.objects.filter(type=type).filter(hour=hour)

                    if len(object) == 0:
                        # Crear el en la db si no existe
                        self.__model.objects.create(hour=hour, type=type, image=image)
                    else:
                        # Actualizar la imagen
                        self.__model.objects.filter(type=type).filter(hour=hour).update(image=image)
                        shutil.copyfile(f'{image}', f'media/{image}')
