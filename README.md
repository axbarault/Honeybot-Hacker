# HoneyBot Hacker - v2.0

## Introduction

Cette repository expose le code source du bot Discord du club **Honeypot Hacker** de Polytech Angers.

Ecrit en Python, ce bot est prêt à l'emploi et est organisé sous forme de modules pour garder une codebase claire et lisible et faciliter la contribution.


## Features

De nombreux projets d'extension sont à prévoir pour le futur. Tous les modules actuellement présents peuvent être customisés à votre guise depuis les fichiers de configuration générés lors du premier démarrage.

Actuellement, le bot propose les modules suivants :

| Nom du module    | Description                                                                                                                                                          |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Verification     | Système de vérification des nouveaux membres demandant l'acceptation des règles du serveur                                                                           |
| Utilities        | Contient de nombreuses commandes utiles (e.i. Pages d'aides générées automatiquement, liens aux réseaux sociaux, descriptions de channels et/ou d'utilisateurs, ...) |
| SiteLeaderboards | Établie un classement interne du serveur sur divers sites de challenges. Implémente des commandes pour lier un profile et voir les détails de celui-ci               |
| Fun              | Ajoute diverses commandes pas vraiment utiles mais très amusantes                                                                                                    |

Pour en apprendre davantage sur les extensions et les commandes, tout est accessible depuis le bot via la commande $help.


## Installation

Le bot est prêt à l'emploi. Pour l'installer sur l'appareil de votre choix, il vous faudra avoir installé **Python 3.9+**. Avoir accès à **Git** permettra également de toujours avoir accès aux dernières mises à jour.

Voici les étapes d'installation à suivre :

0. Rendez-vous dans le dossier où vous souhaiter réaliser l'installation 
1. Clonez la repository : ``git clone https://github.com/axbarault/Honeybot-Hacker.git``
2. Installez les bibliothèques nécessaires : ``pip install discord.py requests``
3. **[UNIX]** Créez un fichier ``start.sh`` comme suit :
```shell
#!/bin/sh

git pull
python3 __main__.py
```
3. **[WINDOWS]** Créez un fichier ``start.cmd`` comme suit :
```commandline
git pull
python __main__.py
```
4. Des fichiers de configuration auront alors été générés dans le dossier ``./resources/``. Vous pourrez indiquer les informations spécifiques à votre utilisation (Bot token, canal et rôle de vérification, ...) dans le fichier ``./resources/config.json``. Un redémarrage du bot est nécessaire pour appliquer les changements réalisés.

*PS : Il est possible que la configuration ne soit pas complètement générée tant que vous n'entrez pas un token valide pour votre bot.*
