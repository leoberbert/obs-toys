from __future__ import annotations

import os


_TRANSLATIONS = {
    "pt_BR": {
        "Back": "Voltar",
        "Search plugins": "Pesquisar plugins",
        "OBS system profile not detected.": "Perfil do OBS no sistema nao detectado.",
        "Refresh": "Atualizar",
        "Welcome to OBS Toys": "Bem-vindo ao OBS Toys",
        "A friendly app for installing OBS plugins on Linux.": "Um aplicativo amigavel para instalar plugins do OBS no Linux.",
        "No plugins found": "Nenhum plugin encontrado",
        "Try another search term to see more plugins.": "Tente outro termo de busca para ver mais plugins.",
        "Status": "Status",
        "Location": "Localizacao",
        "Plugin Details": "Detalhes do Plugin",
        "Install Plugin": "Instalar Plugin",
        "Remove Plugin": "Remover Plugin",
        "Project Page": "Pagina do Projeto",
        "Installed": "Instalado",
        "Not installed": "Nao instalado",
        "OBS is currently open": "O OBS esta aberto no momento",
        "Please close OBS before installing plugins. OBS Toys can try to close it for you and continue the installation.": "Feche o OBS antes de instalar plugins. O OBS Toys pode tentar fecha-lo para voce e continuar a instalacao.",
        "Cancel": "Cancelar",
        "Close OBS and Install": "Fechar OBS e Instalar",
        "Could Not Close OBS": "Nao Foi Possivel Fechar o OBS",
        "OBS Toys could not close OBS automatically. Please close it manually and try again.": "O OBS Toys nao conseguiu fechar o OBS automaticamente. Feche manualmente e tente novamente.",
        "This will download the plugin release and copy its files into your OBS system profile.": "Isso vai baixar a versao do plugin e copiar os arquivos para o perfil do OBS no sistema.",
        "Plugin Installed": "Plugin Instalado",
        "Installation Failed": "Falha na Instalacao",
        "This will remove the plugin files from your OBS system profile.": "Isso vai remover os arquivos do plugin do seu perfil do OBS no sistema.",
        "Plugin Removed": "Plugin Removido",
        "Removal Failed": "Falha na Remocao",
        "Installed at {path}": "Instalado em {path}",
        "Not installed in the system OBS profile.": "Nao instalado no perfil do OBS no sistema.",
        "system OBS profile": "perfil do OBS no sistema",
        "{name} installed into {path}": "{name} instalado em {path}",
        "{name} is already absent from {path}": "{name} ja nao esta presente em {path}",
        "{name} removed from {path}": "{name} removido de {path}",
        "Install {name}?": "Instalar {name}?",
        "Remove {name}?": "Remover {name}?",
        "OK": "OK",
    }
}


def get_language() -> str:
    for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key, "").strip()
        if not value:
            continue
        normalized = value.split(":")[0].split(".")[0]
        if normalized.lower().startswith("pt_br") or normalized.lower().startswith("pt"):
            return "pt_BR"
    return "en"


def translate(message: str, **kwargs: object) -> str:
    language = get_language()
    translated = _TRANSLATIONS.get(language, {}).get(message, message)
    if kwargs:
        return translated.format(**kwargs)
    return translated


_ = translate
