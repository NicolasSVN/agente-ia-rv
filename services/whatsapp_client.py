"""
Cliente para a API WAHA (WhatsApp HTTP API).
Permite enviar e receber mensagens via WhatsApp.
"""
import httpx
from typing import Optional
from core.config import get_settings

settings = get_settings()


class WhatsAppClient:
    """Cliente para interação com a API WAHA."""
    
    def __init__(self):
        self.base_url = settings.WAHA_API_URL.rstrip('/')
        self.api_key = settings.WAHA_API_KEY
        self.session = settings.WAHA_SESSION
    
    def _get_headers(self) -> dict:
        """Retorna headers de autenticação para a API WAHA."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers
    
    async def send_message(self, to: str, message: str) -> dict:
        """
        Envia uma mensagem de texto para um número de WhatsApp.
        
        Args:
            to: Número de telefone no formato internacional (ex: 5511999999999@c.us)
            message: Texto da mensagem a ser enviada
            
        Returns:
            Resposta da API WAHA com campos padronizados:
            - success: bool
            - error: str (se houver erro)
            - error_code: str (código do erro)
            - raw_response: dict (resposta original da API)
        """
        url = f"{self.base_url}/api/sendText"
        
        phone_clean = ''.join(filter(str.isdigit, to))
        chat_id = to if "@c.us" in to else f"{phone_clean}@c.us"
        
        payload = {
            "chatId": chat_id,
            "text": message,
            "session": self.session
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=30.0)
                raw_data = response.json() if response.content else {}
                
                if response.status_code >= 400:
                    error_msg = raw_data.get("message", raw_data.get("error", f"HTTP {response.status_code}"))
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": f"HTTP_{response.status_code}",
                        "raw_response": raw_data,
                        "status_code": response.status_code
                    }
                
                if raw_data.get("error"):
                    return {
                        "success": False,
                        "error": raw_data.get("error"),
                        "error_code": raw_data.get("code", "API_ERROR"),
                        "raw_response": raw_data
                    }
                
                return {
                    "success": True,
                    "raw_response": raw_data,
                    "message_id": raw_data.get("id", raw_data.get("key", {}).get("id"))
                }
                
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "error": "Timeout ao conectar com o servidor WhatsApp",
                    "error_code": "TIMEOUT"
                }
            except httpx.ConnectError as e:
                return {
                    "success": False,
                    "error": f"Não foi possível conectar ao servidor WAHA: {self.base_url}",
                    "error_code": "CONNECTION_ERROR",
                    "details": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": "HTTP_ERROR"
                }
    
    async def send_file(self, to: str, file_url: str, file_type: str, caption: str = "", filename: str = "") -> dict:
        """
        Envia um arquivo (imagem, documento, vídeo ou áudio) para um número de WhatsApp.
        
        Args:
            to: Número de telefone no formato internacional
            file_url: URL do arquivo a ser enviado
            file_type: Tipo do arquivo (image, document, video, audio)
            caption: Legenda do arquivo (opcional)
            filename: Nome do arquivo (para documentos)
            
        Returns:
            Resposta da API WAHA
        """
        phone_clean = ''.join(filter(str.isdigit, to))
        chat_id = to if "@c.us" in to else f"{phone_clean}@c.us"
        
        endpoint_map = {
            'image': '/api/sendImage',
            'video': '/api/sendVideo',
            'audio': '/api/sendVoice',
            'document': '/api/sendFile'
        }
        
        endpoint = endpoint_map.get(file_type, '/api/sendFile')
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "chatId": chat_id,
            "session": self.session
        }
        
        if file_type == 'document':
            payload["file"] = {"url": file_url}
            if filename:
                payload["file"]["filename"] = filename
            if caption:
                payload["caption"] = caption
        elif file_type == 'audio':
            payload["file"] = {"url": file_url}
        else:
            payload["file"] = {"url": file_url}
            if caption:
                payload["caption"] = caption
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=60.0)
                raw_data = response.json() if response.content else {}
                
                if response.status_code >= 400:
                    error_msg = raw_data.get("message", raw_data.get("error", f"HTTP {response.status_code}"))
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": f"HTTP_{response.status_code}",
                        "raw_response": raw_data,
                        "status_code": response.status_code
                    }
                
                if raw_data.get("error"):
                    return {
                        "success": False,
                        "error": raw_data.get("error"),
                        "error_code": raw_data.get("code", "API_ERROR"),
                        "raw_response": raw_data
                    }
                
                return {
                    "success": True,
                    "raw_response": raw_data,
                    "message_id": raw_data.get("id", raw_data.get("key", {}).get("id"))
                }
                
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "error": "Timeout ao enviar arquivo",
                    "error_code": "TIMEOUT"
                }
            except httpx.ConnectError as e:
                return {
                    "success": False,
                    "error": f"Não foi possível conectar ao servidor WAHA: {self.base_url}",
                    "error_code": "CONNECTION_ERROR",
                    "details": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": "HTTP_ERROR"
                }

    async def send_seen(self, chat_id: str) -> dict:
        """Marca uma mensagem como lida."""
        url = f"{self.base_url}/api/sendSeen"
        payload = {
            "chatId": chat_id,
            "session": self.session
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=30.0)
                return response.json()
            except httpx.HTTPError as e:
                return {"error": str(e)}
    
    async def start_typing(self, chat_id: str) -> dict:
        """Inicia indicador de digitação."""
        url = f"{self.base_url}/api/startTyping"
        payload = {
            "chatId": chat_id,
            "session": self.session
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=30.0)
                return response.json()
            except httpx.HTTPError as e:
                return {"error": str(e)}
    
    async def stop_typing(self, chat_id: str) -> dict:
        """Para indicador de digitação."""
        url = f"{self.base_url}/api/stopTyping"
        payload = {
            "chatId": chat_id,
            "session": self.session
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers(), timeout=30.0)
                return response.json()
            except httpx.HTTPError as e:
                return {"error": str(e)}
    
    async def check_connection(self) -> dict:
        """Verifica a conexão com a API WAHA."""
        url = f"{self.base_url}/api/sessions"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers(), timeout=10.0)
                response.raise_for_status()
                return {"success": True, "sessions": response.json()}
            except httpx.HTTPError as e:
                return {"success": False, "error": str(e)}


# Instância global do cliente
whatsapp_client = WhatsAppClient()
