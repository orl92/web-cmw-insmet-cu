import os
import shutil
import subprocess
import threading
import time


# from werkzeug.utils import secure_filename
#
# from dashboard.templatetags.my_filters import filename


class FileObs:
    # Bloqueo a nivel de clase para todas las instancias
    _download_lock = threading.Lock()

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
        self.max_retries = 3
        self.retry_delay = 5  # segundos entre reintentos

    def descargar_archivos_por_hora(self, hora, station_number):
        number = str(station_number)[2:]
        # Validar hora
        if hora not in self.horas_validas:
            raise ValueError(f"Hora inválida. Usa una de: {self.horas_validas}")
        else:
            if hora in ["00", "06", "12", "18"]:
                filename = f'SM{number}.{hora}'
            elif hora in ["03", "09", "15", "31"]:
                filename = f'SI{number}.{hora}'
            else:
                filename = None

        # Sanitize filename to prevent path traversal or dangerous characters
        if filename is not None:
            filename = os.path.basename(os.path.normpath(str(filename)))

        # Crear directorios (temp y final)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.FINAL_DIR, exist_ok=True)

        # Configuración robusta de LFTP
        comando = f"""
            set ftp:ssl-allow yes;
            set ssl:verify-certificate no;
            set ftp:ssl-protect-data yes;
            set ftp:ssl-protect-list yes;
            set ftp:ssl-force yes;
            set ftp:ssl-auth TLS;
            set net:connection-limit 1;
            set net:timeout 60;
            set xfer:clobber on;
            set net:reconnect-interval-base 15;
            set net:max-retries 2;
            cd '{self.REMOTE_DIR}';
            get {filename} -o {self.TEMP_DIR}/{filename};  # Ruta completa de destino
            bye
            """

        # Intentar la descarga con bloqueo y reintentos
        for attempt in range(self.max_retries):
            try:
                with self._download_lock:  # Bloquea el acceso concurrente
                    print(f"⏳ [Intento {attempt + 1}] Descargando {filename}...")

                    # Limpiar directorio temporal antes de cada intento
                    self.limpiar_directorio_temporal()
                    os.makedirs(self.TEMP_DIR, exist_ok=True)

                    # Ejecutar LFTP
                    resultado = subprocess.run(
                        ["lftp", "-u", f"{self.USER},{self.PASS}", "-p", self.PORT,
                         f"ftps://{self.HOST}", "-e", comando],  # FTPS explícito
                        check=True,
                        text=True,
                        capture_output=True,
                        timeout=90
                    )

                    # Verificar si el archivo se descargó correctamente
                    temp_file = os.path.join(self.TEMP_DIR, filename)
                    if os.path.exists(temp_file):
                        # Normalize and validate the temp file path
                        temp_file_norm = os.path.normpath(os.path.abspath(temp_file))
                        temp_dir_norm = os.path.normpath(os.path.abspath(self.TEMP_DIR))
                        if not temp_file_norm.startswith(temp_dir_norm + os.sep):
                            raise Exception("Invalid temp file path: path traversal detected")
                        destino = os.path.join(self.FINAL_DIR, filename)
                        # Normalize and validate the destination path
                        destino_norm = os.path.normpath(os.path.abspath(destino))
                        final_dir_norm = os.path.normpath(os.path.abspath(self.FINAL_DIR))
                        if not destino_norm.startswith(final_dir_norm + os.sep):
                            raise Exception("Invalid file path: path traversal detected")
                        shutil.move(temp_file_norm, destino_norm)
                        print(f"✓ Descarga completada: {filename}")
                        return destino_norm
                    else:
                        raise Exception(f"Archivo {filename} no se descargó correctamente")

            except subprocess.CalledProcessError as e:
                error_msg = f"❌ Error en descarga (intento {attempt + 1}): {e.stderr}"
                print(error_msg)
                if attempt == self.max_retries - 1:
                    raise Exception(f"Fallo después de {self.max_retries} intentos. Último error: {error_msg}")
                time.sleep(self.retry_delay)

            except Exception as e:
                print(f"❌ Error inesperado: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)

    def limpiar_directorio_temporal(self):
        """Limpia el directorio temporal de forma segura"""
        try:
            if os.path.exists(self.TEMP_DIR):
                shutil.rmtree(self.TEMP_DIR)
        except Exception as e:
            print(f"⚠️ Error limpiando directorio temporal: {str(e)}")
