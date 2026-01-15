IA_LLM_ENDPOINTS = {
    "tipifica": "/tipifica-denuncia/{uuid:s}",
    "personal-data": "/personal-data-recover/{uuid:s}",
    "interpretation": "/interpretation/{uuid:s}",
    "upload_expte": "/collection/{uuid:s}/upload",
    "load-context": "/collection/{uuid:s}/load-context",
    "clear-expte": "/collection/{uuid:s}",
    "reset-expte": "/collection/{uuid:s}/reset",
    "chat": "/chat/{uuid:s}",

    "openai-upload-expte": "/openai/collection/{uuid:s}/upload",
    "openai-chat": "/openai/chat/{uuid:s}/{vs_id:s}",
    "openai-interpretation": "/openai/interpretation/{vs_id:s}",
    "openai-personal-data": "/openai/personal-data-recover/{vs_id:s}",

    "upload-knowledge": "/upload-knowledge",
}
