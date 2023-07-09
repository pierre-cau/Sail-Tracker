# Tracker de flotte

<!-- on met le logo en haut de la page -->
![Logo](Tracker_fleet_YCC/images/fleetyytack_withlogo_withbg.png)

## Table des matières

- [Propriétaire](#propriétaire)
- [Description](#description)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Contribuer](#contribuer)
- [Licence](#licence)

## Propriétaire

L'intégralité du projet est la propriété du [**Yacht Club Classique**](https://www.yachtclubclassique.com/).
Ce dernier a été développé dans son intégralité par [**Pierre CAU**](
https://www.linkedin.com/in/pierre-cau), étudiant ingénieur à [l'École Centrale de Lyon](https://www.ec-lyon.fr/).
Pour toute question/problème, veuillez vous adresser à l'adresse suivante : [pcaupro@gmail.com](mailto:pcaupro@gmail.com)

## Description

Ce petit projet personnel a pour but de créer un tracker de flotte. Il permettra de suivre les différents mouvements de la flotte du [**Yacht Club Classique**](https://www.yachtclubclassique.com/).

## Installation

Pour installer le projet, il suffit de cloner le dépôt git sur votre machine. Pour cela, il faut utiliser la commande suivante :

```bash
git clone
```

## Utilisation

Pour utiliser le projet, il suffit de lancer le fichier `main.py` avec la commande suivante une fois avoir bien vérifié que la localisation du répertoire du projet correspond avec celle du répertoire courant via la commande `cd` (pour les utilisateurs de Windows) :

```bash
python main.py
```

## Contribuer

Pour contribuer au projet, il suffit de faire une pull request sur le dépôt git.

## Licence

Pour plus d'informations sur la licence, veuillez vous référer au fichier `Tracker_fleet_YCC/LICENSE.txt`.

``` text
MIT License
```

## Objectifs du projet

La première version du projet a pour but de créer un tracker de flotte. Afin de pouvoir suivre ces même bateaux, il faut pouvoir les identifier. Pour cela, il faut créer un système d'identification des bateaux. Ce système doit être simple et facilement identifiable. Il doit également être facilement modifiable. En effet, il est possible que la flotte du [**Yacht Club Classique**](https://www.yachtclubclassique.com/) évolue. Il faut donc pouvoir ajouter ou supprimer des bateaux facilement.
Ainsi les objectifs du projet sont les suivants :

- Créer un système d'identification des bateaux
- Créer un système de suivi des bateaux

## Mise en place du projet

### Système d'identification des bateaux

Pour identifier les bateaux, j'ai décidé de passer par le ***numéro MMSI*** de ces derniers. Les ***numéros MMSI*** sont systématiquement attribués aux bateaux de plaisance. Ils sont composés de **9 chiffres**. Ils sont attribués par [l'ANFR](https://www.anfr.fr/) (Agence Nationale des Fréquences) et constitue une sorte de "plaque d'immatriculation" pour les bateaux. Ils sont utilisés pour les communications VHF et pour la localisation des bateaux.

### Système de suivi des bateaux

Une fois le système d'identification des bateaux mis en place, il faut pouvoir suivre ces derniers. Pour cela, j'ai cherché à récupérer les données ***AIS (Automatic Identification System)*** des bateaux. Les données ***AIS*** sont des données de positionnement des bateaux. Elles sont émises par les bateaux et reçues par des stations à terre. Ces données sont ensuite transmises à des serveurs qui les rendent accessibles au public. Il existe plusieurs serveurs qui permettent d'accéder à ces données. J'ai choisi d'utiliser le serveur [**MarineTraffic**](https://www.marinetraffic.com/). Ce dernier permet d'accéder aux données AIS de manière "gratuite et facile". Il suffit de créer un compte et de récupérer une clé API. Cette clé API permet d'accéder aux données AIS des bateaux. Il suffit ensuite de faire une requête à l'API pour récupérer les données AIS des bateaux. Ces données sont au format `JSON`.

Il convient de noter que les données AIS ne sont pas disponibles pour tous les bateaux. En effet, il faut que ces derniers soient équipés d'un émetteur AIS. Il faut aussi qu'ils soient dans une zone couverte par les stations AIS. Enfin, il faut qu'ils soient en fonctionnement. Ainsi, il est possible, et même très probable, que certains bateaux ne soient pas suivis par le système. C'est pourquoi, il est nécessaire de mettre en place un système de suivi alternatif à terme.

Une solution possible serait de mettre en place un système de suivi par GPS. Ce système permettrait de suivre les bateaux même s'ils ne sont pas équipés d'un émetteur AIS. Cependant, ce système est plus coûteux et plus complexe à mettre en place. Il nécessite notamment de mettre en place un système de communication entre les bateaux et les serveurs. Un système de stockage des données sera également nécessaire. Alors qu'une API 'open source' permet d'accéder aux données AIS très rapidement et totalement gratuitement.

En outre, il est possible d'utiliser des alternativse en passant par les canaux de communication VHF afin de s'affranchir de la porté des récepteur AIS terrestre si on suit les bateaux en mer. 

### Récupération des données AIS

Pour récupérer et traiter les données AIS ainsi que gérer l'automatisation de cette tâche, deux fichiers ont été créés :

- `tracker.ipynb` : ce notebook permet de visualiser la méthode de récupération et de traitement des données AIS. Il permet également de tester le bon fonctionnement de cette méthode et de visualiser les résultats obtenus.

- `tracker_tools.py` : ce fichier, quant à lui, défini (entre autres) la classe DataBase qui permet de récupérer et de traiter les données AIS en faisant le lien avec la base de données définissant la flotte du [**Yacht Club Classique**](https://www.yachtclubclassique.com/). Il permet également de gérer l'automatisation de cette tâche.

### Génération de la carte interactive 

Pour générer la carte interactive, j'ai utilisé la librairie [**Folium**](https://python-visualization.github.io/folium/). Cette librairie permet de générer des cartes interactives en utilisant les données de [**OpenStreetMap**](https://www.openstreetmap.org/). J'y ai ensuite ajouté les données AIS des bateaux et quelques extras (marqueurs, popup, etc.).

Vous trouverez dans le fichier `tracker_tools.py` la classe `TrackerServer` qui permet de générer la carte interactive via la méthode `generate_html_()`.

## Résultats

Le résultat du programme est une carte interactive qui permet de suivre les bateaux de la flotte du [**Yacht Club Classique**](https://www.yachtclubclassique.com/). Le fichier `index.html` est la carte interactive générée par le programme. Vous pouvez également la retrouver à l'adresse suivante :

- [**https://pierre-cau.github.io/FleetyTracker/index.html**](https://pierre-cau.github.io/FleetyTracker/)

<!-- On ajoute une vidéo de démonstration -->
! [Démonstration] (Tracker_fleet_YCC/images/Tuto_site.mp4)

## Sources

- [**Yacht Club Classique**](https://www.yachtclubclassique.com/)
- [**ANFR**](https://www.anfr.fr/)
- [**MarineTraffic**](https://www.marinetraffic.com/)
- [**OpenStreetMap**](https://www.openstreetmap.org/)
- [**Folium**](https://python-visualization.github.io/folium/)
- [**Wikipedia AIS**](https://fr.wikipedia.org/wiki/Automatic_Identification_System)
- [**Wikipedia MMSI**](https://fr.wikipedia.org/wiki/Maritime_Mobile_Service_Identity)

