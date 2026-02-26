# Logs do Deploy - Tentativa 6

**Data:** 2026-02-26
**Resultado:** FALHOU (health check timeout)

## Configuração aplicada nesta tentativa

Alterações feitas no `.replit` antes deste deploy:
1. Removida segunda entrada `[[ports]]` (localPort=9876, externalPort=3000)
2. Adicionado `healthcheckPath = "/health"` ao bloco `[deployment]`

Configuração do `.replit` (seções relevantes):
```toml
[[ports]]
localPort = 5000
externalPort = 80

[deployment]
deploymentTarget = "vm"
run = ["python", "main.py"]
healthcheckPath = "/health"
```

Uvicorn configurado em `main.py` linha 1181:
```python
config = uvicorn.Config(app, host="0.0.0.0", port=5000, log_level="info")
```

## Logs completos do deploy (todas as linhas)

```
1772110370350 [Info]  starting up user application
1772110370350 [Info]  metasidecar: loaded enterprise status from environment is_enterprise=false
1772110370353 [Info]  forwarding local port 5000 to external port 80 (mapped as 1104)
1772110381594 [Error] [SHIM] Health check shim ativo na porta 5000
1772110381594 [Error] INFO:     Waiting for application startup.
1772110381594 [Error] INFO:     Started server process [27]
1772110383835 [Error] INFO:     Application startup complete.
1772110391596 [Error] [SHIM] Health check shim parado — uvicorn operacional.
```

**Total: 8 linhas de log.**

## Timestamps convertidos

| Timestamp (ms)  | Tempo relativo | Evento |
|-----------------|----------------|--------|
| 1772110370350   | t=0.0s         | Aplicação iniciando |
| 1772110370350   | t=0.0s         | Metasidecar carregado |
| 1772110370353   | t=0.003s       | Port forwarding: 5000 → 80 (mapped as 1104) |
| 1772110370937   | t=0.6s         | **[SHIM] ativo na porta 5000** |
| 1772110381594   | t=11.2s        | Uvicorn started (processo 27) |
| 1772110381594   | t=11.2s        | Waiting for startup |
| 1772110383835   | t=13.5s        | **Application startup complete** |
| 1772110391596   | t=21.2s        | **[SHIM] parado — uvicorn operacional** |

## Análise

### O que apareceu:
- `[SHIM] Health check shim ativo na porta 5000` — shim subiu em t=0.6s ✅
- `[SHIM] Health check shim parado` — shim desligou em t=21.2s ✅
- Uvicorn completou startup em t=13.5s ✅

### O que NÃO apareceu:
- **ZERO linhas `[SHIM] Conexão aceita de ...`** — nenhuma conexão TCP chegou ao shim
- **ZERO linhas `[SHIM] Resposta enviada para ...`** — shim nunca respondeu nada
- **ZERO linhas `[ACCESS] ...`** — nenhum request HTTP chegou ao uvicorn
- **ZERO linhas de `[INIT]`** — lazy router init não aparece nos logs (pode ser stdout vs stderr)

### Conclusão:

O health check do Replit **nunca conectou na porta 5000** durante os 21 segundos de observação. O shim estava ativo e pronto para responder, mas nenhuma conexão TCP foi recebida. O uvicorn também ficou operacional a partir de t=13.5s e nenhum request chegou.

Isso descarta problemas de código (shim bloqueando, endpoint retornando erro, etc.) — o problema é que **o tráfego do health check não está alcançando a porta 5000 da aplicação**.

## Hipóteses restantes

1. **Health check usa porta diferente de 5000**: O log mostra "mapped as 1104" — é possível que o health checker interno bata na porta 1104, que o proxy do Replit deveria redirecionar para 5000. Se esse redirecionamento não funcionar durante o cold start, o health check nunca chega.

2. **Health check bate no proxy externo (porta 80)**: Se o health checker testa a porta 80 externamente, e o proxy do Replit só conecta na porta 5000 após considerar a app "saudável", cria-se um deadlock — o proxy espera o health check passar, mas o health check depende do proxy.

3. **`healthcheckPath = "/health"` não é suportado para VM deployments**: A documentação do Replit não confirma explicitamente que este campo existe. Se for ignorado, o health check pode estar usando um mecanismo diferente (TCP connect puro sem HTTP GET).

4. **Timeout do health check é menor que o cold start**: Se o Replit espera resposta em <5s e o shim só sobe em t=0.6s, pode haver uma janela entre t=0 e t=0.6s onde o check já falhou.

## Próximos passos sugeridos

1. **Testar com bind na porta 1104 além da 5000**: Adicionar um listener TCP na porta 1104 para verificar se o health check chega lá.
2. **Contatar suporte Replit**: Perguntar especificamente qual porta e protocolo o health checker usa para VM deployments.
3. **Testar com app minimal**: Criar um `main.py` de 5 linhas (apenas uvicorn + rota `/`) para isolar se o problema é do cold start lento ou da configuração.
