# Spotify CLI(Unofficial)

* A simple CLI application to communicate with the Spotify Web API via the command line.
* Works on windows, linux, Mac etc.

> NB: In order to support the spotify interactive plogin page, the host should have atleast one web browser installed.

#### Example Usage

```bash

# Opens spotify login page using your defalt browser
spt login

# Retrieves your saved albums
spt library GetSavedAlbums --limit 10
```

## Pre-requisites

* Make sure you have installed python 3.6x (Make sure it is added to the system path)
* Install pip if you have not already done so
* Any modern web browser(This is very importan)


## Getting started

* Install latest package using pip

````bash
pip install --upgrade spt
````
