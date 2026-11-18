import json
import logging
import os
import pwd
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", "8080"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
APP_NOME = os.environ.get("APP_NOME", "servico-so")

logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(APP_NOME)


def usuario_atual():
  try:
    return pwd.getpwuid(os.getuid()).pw_name
  except KeyError:
    return "desconhecido"


class Handler(BaseHTTPRequestHandler):

  def _responder(self, codigo, corpo, tipo="text/plain; charset=utf-8"):
    dados = corpo.encode("utf-8")
    self.send_response(codigo)
    self.send_header("Content-Type", tipo)
    self.send_header("Content-Length", str(len(dados)))
    self.end_headers()
    self.wfile.write(dados)

  def do_GET(self):
    cliente = self.client_address[0]
    if self.path == "/":
      log.info("requisicao GET / de %s -> 200", cliente)
      self._responder(
          200,
          f"{APP_NOME} funcionando (PID {os.getpid()}, UID {os.getuid()})\n",
      )
    elif self.path == "/status":
      info = {
          "app": APP_NOME,
          "pid": os.getpid(),
          "ppid": os.getppid(),
          "uid": os.getuid(),
          "gid": os.getgid(),
          "usuario": usuario_atual(),
          "porta": PORT,
          "log_level": LOG_LEVEL,
      }
      log.info("requisicao GET /status de %s -> 200", cliente)
      log.debug("status detalhado: %s", info)
      self._responder(
          200, json.dumps(info, indent=2) + "\n", "application/json"
      )
    elif self.path == "/falha":
      log.error(
          "falha controlada solicitada por %s: encerrando com codigo 1", cliente
      )
      self._responder(
          500, "falha controlada: processo encerrando com codigo 1\n"
      )
      threading.Timer(0.5, lambda: os._exit(1)).start()
    else:
      log.warning("requisicao GET %s de %s -> 404", self.path, cliente)
      self._responder(404, "rota nao encontrada\n")

  def log_message(self, formato, *args):
    pass


def parar(signum, _frame):
  log.info(
      "sinal %s recebido (parada normal): encerrando com codigo 0",
      signal.Signals(signum).name,
  )
  sys.exit(0)


def main():
  signal.signal(signal.SIGTERM, parar)
  signal.signal(signal.SIGINT, parar)

  servidor = HTTPServer(("0.0.0.0", PORT), Handler)
  log.info(
      "iniciando %s: pid=%s uid=%s usuario=%s porta=%s log_level=%s",
      APP_NOME,
      os.getpid(),
      os.getuid(),
      usuario_atual(),
      PORT,
      LOG_LEVEL,
  )
  try:
    servidor.serve_forever()
  finally:
    servidor.server_close()


if __name__ == "__main__":
  main()
