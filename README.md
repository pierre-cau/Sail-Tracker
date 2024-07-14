<!-- on met le logo en haut de la page -->
<div align="center">
  <img src="Tracker_fleet_YCC\images\Logo_FleetyTrack\sansBG\Logo_fleetytrack_txt_H_sansBG.svg" alt="logo" width="auto" height="80" display="block"/>
</div>

# Fleet Tracker 🔎

###### Wondering how to track your fleet❔...You're in the right place🔥!

<div align="center">
  <img src="Tracker_fleet_YCC\images\Logo_FleetyTrack\sansBG\Logo_fleetytrack_sansBG.svg" alt="logo" width="200" height="200" display="block"/> 

<p>
  <img src="https://www.svgrepo.com/show/303205/html-5-logo.svg" alt="html" width="30" height="30"/>
  <img src="https://www.svgrepo.com/show/452185/css-3.svg" alt="css" width="30" height="30"/>
  <img src="https://www.svgrepo.com/show/349419/javascript.svg" alt="js" width="30" height="30"/>
  <img src="https://stormglass.io/wp-content/uploads/2019/05/Stormglass-Circle-1400.svg" height="30" alt="storm-glass">
  <img src="https://www.svgrepo.com/show/452091/python.svg" height="30" alt="python">
  <img src="https://cdn.svgporn.com/logos/leaflet.svg" height="30" alt="leaflet-maps">
</p>
</div>

<div height="30" align="center">
  <a href="https://github.com/pierre-cau/Sail-Tracker">
    <img src="https://img.shields.io/badge/Version-1.0.0-blue" alt="version">
  </a>
  <a href="https://github.com/pierre-cau/Sail-Tracker/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/pierre-cau/Sail-Tracker" alt="license">
  </a>
  <img src="https://img.shields.io/badge/Status-In%20Progress-orange" alt="status">
</div>

## Ownership 📝

The entire project is owned by the [**Classic Yacht Club**](https://www.yachtclubclassique.com/).
It was fully developed by [**Pierre CAU**](https://www.linkedin.com/in/pierre-cau), an engineering student at [École Centrale de Lyon](https://www.ec-lyon.fr/).
For any questions/issues, please contact the following address: [pcaupro@gmail.com](mailto:pcaupro@gmail.com)

## License ©️🔒

For more information about the license, please refer to the `Tracker_fleet_YCC/LICENSE.txt` file.

``` text
MIT License
```

## Project Description 📚

This small personal project aims to create a fleet tracker. It will allow tracking the various movements of the fleet of the [**Classic Yacht Club**](https://www.yachtclubclassique.com/).
## Installation 🔧

To install the project, simply clone the git repository to your machine. To do this, use the following command:

```bash
git clone
```

## Contributing to the Project 🤝

To contribute to the project, simply make a pull request on the git repository.

___

## 📌 Usage

To use the project, simply run the `main.py` file with the following command after ensuring that the project directory location matches the current directory via the `cd` command (for Windows users):

```bash
python main.py
```

## 📌 Project Goals

The first version of the project aims to create a fleet tracker. In order to track these boats, it is necessary to be able to identify them. For this, a boat identification system must be created. This system should be simple and easily identifiable. It must also be easily modifiable. Indeed, the fleet of the [**Classic Yacht Club**](https://www.yachtclubclassique.com/) may evolve. Therefore, it should be possible to easily add or remove boats.
Thus, the project goals are as follows:

- Create a boat identification system
- Create a boat tracking system

## 📌 Project Setup

### Boat Identification System 🆔

To identify the boats, I decided to use their ***MMSI number***. The ***MMSI numbers*** are systematically assigned to pleasure boats. They consist of **9 digits**. They are assigned by [the ANFR](https://www.anfr.fr/) (National Frequency Agency) and serve as a sort of "license plate" for boats. They are used for VHF communications and for locating boats.

### Boat Tracking System 📡

Once the boat identification system is in place, it is necessary to track these boats. For this purpose, I sought to retrieve the ***AIS (Automatic Identification System)*** data of the boats. The ***AIS*** data are positioning data of the boats. They are emitted by the boats and received by land stations. These data are then transmitted to servers that make them accessible to the public. There are several servers that allow access to this data. I chose to use the server [**MarineTraffic**](https://www.marinetraffic.com/). This server allows access to AIS data in a "free and easy" manner. It is enough to create an account and retrieve an API key. This API key allows access to the AIS data of the boats. If the servers are queried with a simple API request, it is then possible to retrieve the AIS data of the boats. These data are in `JSON` format.
Other API solutions (such as [**AIS Hub**](https://www.aishub.net/)) are also conceivable.

It should be noted that AIS data are not available for all boats. Indeed, they must be equipped with an AIS transmitter. They must also be in an area covered by AIS stations. Finally, they must be operational. Thus, it is possible, and even very likely, that some boats will not be tracked by the system. This is why it is necessary to set up an alternative tracking system in the long term.

A possible solution would be to set up a GPS tracking system. This system would allow tracking boats even if they are not equipped with an AIS transmitter. However, this system is more costly and more complex to implement. It requires, in particular, setting up a communication system between the boats and the servers. A data storage system will also be necessary. Whereas an 'open source' API allows access to AIS data very quickly and totally free of charge.

Furthermore, it is possible to use alternatives by going through VHF communication channels to overcome the range of terrestrial AIS receivers if tracking boats at sea.

### AIS Data Retrieval 📥

To retrieve and process AIS data as well as manage the automation of this task, two files have been created:

> `tracker.ipynb`: This notebook allows for the visualization of the method for retrieving and processing AIS data. It also allows for testing the functionality of this method and viewing the obtained results.

> `tracker_tools.py`: This file defines (among other things) the DataBase class, which retrieves and processes AIS data by linking with the database defining the fleet of the [**Classic Yacht Club**](https://www.yachtclubclassique.com/). It also manages the automation of this task.

### Interactive Map Generation 🗺️

To generate the interactive map, I used the [**Folium**](https://python-visualization.github.io/folium/) library. This library allows for the creation of interactive maps using data from [**OpenStreetMap**](https://www.openstreetmap.org/). I then added the AIS data of the boats and some extras (markers, popups, etc.).

You will find in the file `tracker_tools.py` the `TrackerServer` class that allows generating the interactive map via the `generate_html_()` method.

## 📌 Results

The result of the program is an interactive map that allows tracking the boats of the [**Classic Yacht Club**](https://www.yachtclubclassique.com/) fleet. The `index.html` file is the interactive map generated by the program. You can also find it at the following address:

> [*https://pierre-cau.github.io/FleetyTracker*](https://pierre-cau.github.io/FleetyTracker/)

[![Example of using the map](https://github.com/pierre-cau/YCC_fleet_tracker/blob/main/Tracker_fleet_YCC/images/play_tuto.png)](https://youtu.be/e5CfFEt8en8)

## 📝 Notes

This program is a first draft. Therefore, it may evolve over time. It is also possible that there are bugs present. Please do not hesitate to share your comments and suggestions.

## 🔗 Some Useful Links...


>* [**Classic Yacht Club**](https://www.yachtclubclassique.com/)
>* [**ANFR**](https://www.anfr.fr/)
>* [**SHOM**](https://www.shom.fr/)
>* [**SHOM GeoAPI**](https://geoapi.fr/shomgt/tile.php)
>* [**AIS Hub**](https://www.aishub.net/)
>* [**MarineTraffic**](https://www.marinetraffic.com/)
>* [**OpenStreetMap**](https://www.openstreetmap.org/)
>* [**Folium**](https://python-visualization.github.io/folium/)
>* [**Wikipedia AIS**](https://en.wikipedia.org/wiki/Automatic_identification_system)
>* [**Wikipedia MMSI**](https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity)
>* [**Wikipedia GPS**](https://en.wikipedia.org/wiki/Global_Positioning_System)

---
## Contact 📱

[![Github Badge](https://img.shields.io/badge/-Github-000?style=flat-square&logo=Github&logoColor=white&link=https://github.com/gabriellopes00)](https://github.com/pierre-cau)
[![Linkedin Badge](https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white&link=https://www.linkedin.com/in/gabriel-lopes-6625631b0/)](https://www.linkedin.com/in/pierre-cau)
[![Gmail Badge](https://img.shields.io/badge/-Gmail-D14836?&style=flat-square&logo=Gmail&logoColor=white&link=mailto:gabrielluislopes00@gmail.com)](mailto:pcaupro@gmail.com)
[![Facebook Badge](https://img.shields.io/badge/facebook-%231877F2.svg?&style=flat-square&logo=facebook&logoColor=white)](https://www.facebook.com/Pcau22410/)




