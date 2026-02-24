# Auditoria de Dependências de Sistema

**Data:** 2026-02-24  
**Objetivo:** Identificar bibliotecas Python que dependem de binários externos (padrão pdf2image/poppler) e avaliar risco em produção.

---

## 1. Bibliotecas Auditadas (Lista Completa)

| Biblioteca | Binário Necessário | Presente no Código? | Status |
|---|---|---|---|
| pdfkit / wkhtmltopdf | `wkhtmltopdf` | Não | N/A |
| Wand / ImageMagick | `convert` (ImageMagick) | Não | N/A |
| ffmpeg / moviepy / pydub | `ffmpeg` | Não | N/A |
| pytesseract | `tesseract-ocr` | Não | N/A |
| ghostscript | `gs` | Não | N/A |
| cairosvg / cairo | `libcairo2` | Não | N/A |
| weasyprint | `libpango`, `libgdk-pixbuf` | Não | N/A |
| pdf2image | `poppler-utils` (`pdftoppm`) | **Removida** (migrada para PyMuPDF) | Resolvido |
| python-magic | `libmagic` | **Sim** | Risco Médio |
| python-docx | Nenhum (puro Python) | Sim | Seguro |

---

## 2. Dependências com Risco Identificado

### 2.1 python-magic → libmagic

**Localização:** `core/upload_validator.py`

**Dependência:** `python-magic` usa `libmagic` (biblioteca C) via ctypes para detecção de tipo MIME real dos arquivos enviados por upload.

**Mitigação existente:** O código já possui fallback graceful:
```python
try:
    import magic
    _magic_available = True
except ImportError:
    _magic_available = False
```

Quando `libmagic` não está disponível, o validador recorre a detecção por magic bytes (assinatura de arquivo), cobrindo PDF, PNG, JPEG, DOCX e XLSX.

**Risco em produção:** Médio. O fallback funciona para os tipos de arquivo mais comuns, mas é menos robusto que `libmagic` para detectar arquivos malformados ou com extensão falsificada. Em dev, `libmagic` está disponível (via Nix). Em produção (Cloud Run), pode não estar — nesse caso o fallback assume automaticamente.

**Recomendação:** Manter como está. O fallback é adequado e a funcionalidade não é bloqueante.

---

## 3. Dependências Compiladas (sem binários externos)

Estas bibliotecas têm extensões C/C++ mas são distribuídas como wheels pré-compilados — não dependem de binários do sistema operacional:

| Biblioteca | Versão | Extensão | Status Produção |
|---|---|---|---|
| psycopg2-binary | 2.9.9 | C (libpq bundled) | Seguro |
| lxml | 6.0.2 | C (libxml2 bundled) | Seguro |
| bcrypt | 4.0.1 | C | Seguro |
| Pillow | 12.1.0 | C (image libs bundled) | Seguro |
| numpy | 1.26.4 | C/Fortran | Seguro |
| PyMuPDF (fitz) | — | C (MuPDF bundled) | Seguro |
| tiktoken | 0.5.2 | Rust | Seguro |

---

## 4. Dependências Puras Python (zero risco)

| Biblioteca | Função |
|---|---|
| python-docx | Leitura de arquivos DOCX |
| PyPDF2 | Leitura de texto de PDFs |
| openpyxl | Leitura de Excel |
| pandas | Análise de dados |
| beautifulsoup4 | Parsing HTML |
| jinja2 | Templates |
| msal | Auth Microsoft |
| pgvector | Extensão PostgreSQL (driver) |
| slowapi | Rate limiting |
| aiofiles | I/O assíncrono |

---

## 5. Verificação de subprocess

**Resultado:** Zero chamadas a `subprocess` ou `os.system()` encontradas no código Python do projeto. Não há execução de comandos de sistema inline.

---

## 6. Conclusão

| Categoria | Quantidade | Status |
|---|---|---|
| Binários externos perigosos | 0 | Limpo |
| Dependência removida (pdf2image) | 1 | Resolvido |
| Risco médio com fallback (python-magic) | 1 | Monitorar |
| Compiladas com wheels seguros | 7 | Seguro |
| Puras Python | 10+ | Seguro |

**O projeto está limpo de dependências de sistema que possam causar falhas silenciosas em produção.** O único caso anterior (pdf2image/poppler) já foi resolvido. O `python-magic` tem fallback implementado.
