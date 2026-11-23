# Evidências do Trabalho 4 - Sistemas Operacionais

- 01-servico-funcionando.txt: Estado do serviço e listagem completa com docker ps e docker ps -a.
- 02-usuario-e-seguranca.txt: Usuário/UID, Privileged, sistema de arquivos somente leitura (ReadonlyRootfs), capabilities removidas (CapDrop) e processos com docker top.
- 03-falha-e-recuperacao.txt: Registro de falha e recuperação do serviço.
- 04-parada-normal.txt: Encerramento normal e limpeza de recursos.
- 05-limites.txt: Limites de recursos configurados e leitura atual via docker stats.
- 06-configuracao-externa.txt: alteração de LOG_LEVEL (INFO → DEBUG) e da porta publicada (8080 → 8081) pelo .env, sem editar o código, com a resposta do /status confirmando o novo valor.
- 07-logs.txt: Logs completos gerados pelo serviço.
