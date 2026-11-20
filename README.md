# Trabalho 4 – Operacionalização segura de um serviço Linux com Docker

Disciplina: Sistemas Operacionais – Prof. Guibson Krause
Faculdade Serra Dourada – Análise e Desenvolvimento de Sistemas

## Integrantes

- Lucas da Cunha Torres
- Wilbert Moreira Barradas


## Sobre o serviço

Servidor HTTP simples em Python (somente biblioteca padrão) executado em um container Docker.

| Rota      | O que faz                                                                    |
|-----------|------------------------------------------------------------------------------|
| `/`       | Responde que o serviço está funcionando, com PID e UID do processo           |
| `/status` | JSON com app, PID, PPID, UID, GID, usuário, porta e nível de log             |
| `/falha`  | Falha controlada: encerra o processo principal com código de saída 1         |
| outras    | 404 e registro de aviso (WARNING) no log                                     |

## Pré-requisitos

- Linux (testado em Ubuntu XX.XX em VM VirtualBox)
- Docker Engine XX.X e Docker Compose v2 (`docker compose version`)
- git e curl

> Observação de segurança: adicionar o usuário ao grupo `docker` dá a ele acesso equivalente a root no host. Por isso, em ambiente real, o acesso ao Docker deve ser restrito a administradores (ou usar `sudo docker`).

## Estrutura do repositório

```
app/app.py          aplicação
Dockerfile          construção da imagem
compose.yaml        opções de execução (porta, reinício, limites, segurança)
.env.example        modelo de configuração (o .env real não vai para o Git)
evidencias/         saídas de terminal que comprovam cada etapa
```

## Configuração (variáveis de ambiente)

| Variável    | Padrão       | Função                                           |
|-------------|--------------|--------------------------------------------------|
| `PORT`      | `8080`       | Porta em que a aplicação escuta dentro do container |
| `HOST_PORT` | `8080`       | Porta publicada no host                          |
| `LOG_LEVEL` | `INFO`       | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `APP_NOME`  | `servico-so` | Nome exibido pela aplicação e nos logs           |

Os valores ficam no arquivo `.env`, lido pelo Compose (`env_file`). Para alterar qualquer valor, basta editar o `.env` e recriar o container – o código não é modificado. O `.env` está no `.gitignore`; no repositório existe apenas o `.env.example`. Credenciais reais, se houvesse, ficariam somente no `.env` local.

## Segurança e permissões

- **Usuário sem privilégios:** a imagem cria `appuser` (UID 10001, GID 10001, sem shell de login) e usa `USER appuser`. O processo principal roda com UID ≠ 0.
- **Arquivos:** `app.py` pertence ao root com permissão `0644`. O `appuser` só precisa **ler** o código; ele não consegue alterá-lo.
- **Diretórios:** o sistema de arquivos do container é somente leitura (`read_only: true`). A aplicação não grava nada em disco (logs vão para a saída padrão e `PYTHONDONTWRITEBYTECODE=1` evita arquivos `.pyc`).
- **Portas:** a aplicação escuta na 8080. Por ser maior que 1024, não exige privilégio de root nem a capability `NET_BIND_SERVICE`.
- **Capabilities:** todas removidas (`cap_drop: ALL`).
- **Escalada de privilégio:** bloqueada com `no-new-privileges:true`.
- **Modo privilegiado:** não é usado (`privileged: false`).

## Recursos e recuperação

- Limite de memória: 128 MB (`mem_limit: 128m`)
- Limite de CPU: 0,5 núcleo (`cpus: 0.5`)
- Limite de processos: 50 (`pids_limit: 50`)
- Política de reinício: `restart: on-failure` – o Docker reinicia o container quando o processo principal termina com código diferente de 0. A política só passa a valer depois que o container fica pelo menos 10 segundos em execução. `docker stop` (parada normal, código 0) **não** provoca reinício.
- A aplicação trata o sinal SIGTERM. Como ela roda como PID 1 no container, sem esse tratamento o kernel ignoraria o sinal e o `docker stop` só encerraria o processo após 10 s, com SIGKILL.

---

# Runbook

Todos os comandos são executados na raiz do repositório.

### 1. Obter o código e configurar

```bash
git clone https://github.com/davicunhavtx21-afk/TRABALHO4-SO.git
cd TRABALHO4-SO
cp .env.example .env        # ajuste os valores se necessário
```

### 2. Construir a imagem e iniciar

```bash
docker compose up -d --build
```

Equivalente sem Compose:

```bash
docker build -t servico-so:1.0 .
docker run -d --name servico-so --env-file .env -p 8080:8080 \
  --restart on-failure --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --memory 128m --cpus 0.5 --pids-limit 50 servico-so:1.0
```

### 3. Verificar o estado

```bash
docker ps                 # container servico-so com STATUS "Up"
docker ps -a              # inclui containers parados
docker compose ps
```

### 4. Testar a aplicação

URL de teste: http://localhost:8080

```bash
curl http://localhost:8080/
curl http://localhost:8080/status
```

Esperado: resposta 200 com `UID 10001`.

### 5. Verificar o usuário efetivo e a segurança

```bash
docker exec servico-so id
docker top servico-so -eo uid,pid,args
docker inspect -f 'User={{.Config.User}} Privileged={{.HostConfig.Privileged}} ReadOnly={{.HostConfig.ReadonlyRootfs}} CapDrop={{.HostConfig.CapDrop}}' servico-so
docker exec servico-so touch /app/teste     # deve falhar: sistema de arquivos somente leitura
```

Esperado: `uid=10001(appuser)`, `Privileged=false`, `ReadOnly=true`, `CapDrop=[ALL]`.

### 6. Verificar os limites de recursos

```bash
docker inspect -f 'Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCpus}} PidsLimit={{.HostConfig.PidsLimit}}' servico-so
docker stats --no-stream servico-so
docker exec servico-so cat /sys/fs/cgroup/memory.max   # 134217728 = 128 MB
docker exec servico-so cat /sys/fs/cgroup/cpu.max      # 50000 100000 = 0,5 CPU
```

### 7. Consultar os logs

```bash
docker compose logs servico
docker compose logs -f servico      # acompanhar em tempo real (Ctrl+C sai)
docker logs servico-so              # equivalente sem Compose
```

Mensagens esperadas: `iniciando servico-so ...`, `requisicao GET / ... -> 200`, `requisicao GET /xyz ... -> 404` (WARNING).

### 8. Alterar a configuração sem editar o código

```bash
sed -i 's/^LOG_LEVEL=.*/LOG_LEVEL=DEBUG/; s/^HOST_PORT=.*/HOST_PORT=8081/' .env
docker compose up -d --force-recreate
curl http://localhost:8081/status        # log_level agora é DEBUG
docker compose logs servico | grep DEBUG
cp .env.example .env && docker compose up -d --force-recreate   # volta ao padrão
```

### 9. Simular a falha e confirmar a recuperação

```bash
docker inspect -f 'ANTES: RestartCount={{.RestartCount}} StartedAt={{.State.StartedAt}}' servico-so
sleep 12                                   # container precisa estar no ar há 10 s ou mais
curl http://localhost:8080/falha
sleep 3
docker ps -a --filter name=servico-so
docker inspect -f 'DEPOIS: RestartCount={{.RestartCount}} StartedAt={{.State.StartedAt}}' servico-so
docker compose logs --tail 10 servico
curl http://localhost:8080/                # serviço respondendo de novo
```

Esperado: `RestartCount` aumenta em 1, `StartedAt` muda e os logs mostram `falha controlada ... codigo 1` seguido de um novo `iniciando servico-so`.

Atenção: `docker compose up --force-recreate` ou `docker compose down` criam um container novo e zeram o contador de reinícios.

### 10. Parar o serviço

```bash
docker compose stop               # parada normal (SIGTERM, código 0)
docker ps -a --filter name=servico-so     # Exited (0) – não há reinício
docker compose logs --tail 3 servico      # "sinal SIGTERM recebido (parada normal)"
docker compose down               # remove container e rede
```

---

## Limitações do ambiente

- (Preencher se houver. Ex.: VirtualBox em NAT exige redirecionamento de porta para acessar pelo navegador do Windows; aviso de swap no `docker run --memory`.)

## Evidências

Ver a pasta [`evidencias/`](evidencias/) – cada arquivo traz a saída do terminal e o que ela comprova.


