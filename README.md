# **Honeybot Hacker**

Le bot discord du club hacking de Polytech Angers
Fait en Python 3.9

Le début d'une grande aventure…

## Démarrage

La commande `python init_db` est nécessaire pour initialisé la base de données.

Un message avec un règlement doit être présent sur le serveur.

Le bot necessite l'intention 'MEMBERS' activable depuis le [tableau de bord](https://discord.com/developers/applications) de l'application.

## Config

```json
{
    "prefix": "<ton préfixe>",
    "discord-token": "<ton token de bot>",
    "rules-channel-id": <id du salon avec le message de règles>,
    "rules-message-id": <id du message de règles>
}
```
