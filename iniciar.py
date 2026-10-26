from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading, webbrowser
root=Path(__file__).resolve().parent/'work'/'sites'/'r15-ocala'/'dist'
if not (root/'index.html').is_file():
    raise SystemExit('Extrae TODO el ZIP antes de abrir la web.')
server=None
for port in range(8765,8786):
    try:
        server=ThreadingHTTPServer(('127.0.0.1',port),partial(SimpleHTTPRequestHandler,directory=str(root)))
        break
    except OSError: pass
if server is None: raise SystemExit('No hay un puerto local disponible entre 8765 y 8785.')
url=f'http://127.0.0.1:{port}/?lang=es'
print('Rainbow Park Collection: '+url,flush=True)
print('Mantén esta ventana abierta. Para cerrar el servidor: Ctrl+C.',flush=True)
threading.Timer(1,lambda:webbrowser.open(url)).start()
try: server.serve_forever()
except KeyboardInterrupt: pass
finally: server.server_close()
