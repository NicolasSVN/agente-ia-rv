# Bypass de Login Dev — Alteracoes para Reverter

Este documento registra TODAS as alteracoes feitas para o bypass de login em dev.
Para reverter, desfaca cada alteracao na ordem inversa.

---

## Arquivo 1: `api/endpoints/auth.py`

### ADICIONADO: Linhas 30-48 (endpoint /dev-login)

Apos a linha `router = APIRouter(prefix="/api/auth", tags=["Autenticação"])`, foram adicionadas as seguintes linhas:

```python
@router.get("/dev-login")
async def dev_login(request: Request, response: Response, db: Session = Depends(get_db)):
    if IS_PRODUCTION:
        raise HTTPException(status_code=404)
    admin_user = db.query(crud.User).filter(crud.User.role == "admin").first()
    if not admin_user:
        raise HTTPException(status_code=500, detail="Nenhum admin encontrado")
    token_data = {
        "sub": admin_user.username,
        "user_id": admin_user.id,
        "role": admin_user.role,
        "email": admin_user.email or ""
    }
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": admin_user.username, "user_id": admin_user.id})
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(key="access_token", value=access_token, httponly=True, max_age=86400, samesite="lax", path="/", secure=False)
    redirect.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*86400, samesite="lax", path="/api/auth", secure=False)
    return redirect
```

### COMO REVERTER:
Deletar TUDO entre (e incluindo) `@router.get("/dev-login")` ate a linha `return redirect` que vem logo antes de `MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")`. Manter uma linha em branco entre `router = APIRouter(...)` e `MICROSOFT_CLIENT_ID`.

---

## Arquivo 2: `frontend/templates/login.html`

### ADICIONADO: Linhas 112-116 (botao "Entrar como Admin (Dev)")

Antes do `<div class="footer">`, foi adicionado:

```html
        <div id="dev-login-container" style="margin-top: 16px; display: none;">
            <a href="/api/auth/dev-login" class="btn-microsoft" style="display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; padding: 14px; font-size: 1rem; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; color: #92400e; text-decoration: none; font-weight: 500; transition: all 0.2s ease;">
                Entrar como Admin (Dev)
            </a>
        </div>
```

### ADICIONADO: Linhas 138-142 (script para mostrar botao em dev)

Dentro do `<script>`, apos o bloco `if (urlParams.has('error')) { ... }`, foi adicionado:

```javascript
        fetch('/api/auth/dev-login', {redirect: 'manual'}).then(r => {
            if (r.status !== 404) {
                document.getElementById('dev-login-container').style.display = 'block';
            }
        }).catch(() => {});
```

### COMO REVERTER:
1. Deletar o bloco `<div id="dev-login-container">...</div>` inteiro (5 linhas + linha em branco)
2. Deletar o bloco `fetch('/api/auth/dev-login'...)` inteiro (4 linhas + linha em branco) do script

---

## Resumo rapido para reverter TUDO:

1. Em `api/endpoints/auth.py`: deletar o endpoint `dev_login` (linhas 30-48)
2. Em `frontend/templates/login.html`: deletar o div `dev-login-container` e o fetch no script
3. Ou pedir ao agente: "reverta o bypass de login dev"
