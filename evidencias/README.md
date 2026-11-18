# Evidências do Trabalho 4 - Sistemas Operacionais

* *01-servico-funcionando.txt*: Comprova a construção da imagem, arranque do container e resposta das rotas HTTP (/ e /status).
* *02-usuario-e-seguranca.txt*: Comprova que a aplicação roda com utilizador sem privilégios (appuser, UID 10001) e sem modo privilegiado.
* *03-falha-e-recuperacao.txt*: Demonstra o contador de reinícios antes da falha (0), a ativação da rota de falha, o incremento para 1 via restart: on-failure, os logs do erro e o restabelecimento.
* *04-parada-normal.txt*: Regista o encerramento gracioso do serviço e a limpeza completa dos recursos.
