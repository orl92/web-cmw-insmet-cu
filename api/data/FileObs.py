import os
import shutil
import subprocess

from werkzeug.utils import secure_filename

from dashboard.templatetags.my_filters import filename


class FileObs:
    def __init__(self):
        # Configuración
        self.HOST = "10.0.100.224"
        self.USER = "estaciones"
        self.PASS = "CasaB2024*"
        self.PORT = "990"
        self.REMOTE_DIR = "/Reportes Procesados"
        self.TEMP_DIR = "./media/temp"
        self.FINAL_DIR = "./media/obs"
        self.horas_validas = ["00", "03", "06", "09", "12", "15", "18", "21"]

    def descargar_archivos_por_hora(self, hora, station_number):
        number = str(station_number)[2:]
        # Validar hora
        if hora not in self.horas_validas:
            raise ValueError(f"Hora inválida. Usa una de: {self.horas_validas}")

        # Crear directorios (temp y final)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.FINAL_DIR, exist_ok=True)

        # Comando LFTP (descarga en temp)
        comando = f"""
        set ftp:ssl-allow yes;
        set ssl:verify-certificate no;
        cd '{self.REMOTE_DIR}';
        mget SM35[0-5].{hora} -O {self.TEMP_DIR}/;
        mget SI35[0-5].{hora} -O {self.TEMP_DIR}/;
        bye
        """

        # Ejecutar LFTP
        try:
            # print(f"⏳ Descargando archivos .{hora} en {self.TEMP_DIR}...")
            # subprocess.run(
            #     ["lftp", "-u", f"{self.USER},{self.PASS}", "-p", self.PORT, f"ftps://{self.HOST}", "-e", comando],
            #     check=True,
            #     text=True
            # )
            #
            # # Mover archivos de temp a final (sobrescribiendo)
            # archivos_descargados = os.listdir(self.TEMP_DIR)
            # for archivo in archivos_descargados:
            #     origen = os.path.join(self.TEMP_DIR, archivo)
            #     destino = os.path.join(self.FINAL_DIR, archivo)
            #     shutil.move(origen, destino)
            #     print(f"✓ Movido: {archivo}")

            print(f"✅ Descarga completada. Archivos en {self.FINAL_DIR}:")
            print(os.listdir(self.FINAL_DIR))
            for i in os.listdir(self.FINAL_DIR):
                if number in i:
                    file = f'{self.FINAL_DIR}/{i}'
                    return file

        except subprocess.CalledProcessError as e:
            print(f"❌ Error en la descarga: {e}")

    def limpiar_directorio_temporal(self):
        # Limpiar directorio temporal
        if os.path.exists(self.TEMP_DIR):
            shutil.rmtree(self.TEMP_DIR)
