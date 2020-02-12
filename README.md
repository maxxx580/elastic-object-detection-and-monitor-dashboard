# ece1779-a1

## Overview
This project is a python-based web application that allow users to upload images to server and performs object detection on the image. This application is hosted by gunicorn and set to run on port 5000. 

## Group
* Hongyu Liu 1005851295   
* Ran Wang 1006126951   
* Zixiang Ma 1005597285  

------

## Run
```
bash start.sh
```
------

## Major Dependencies
```
Python 3.7
Flaks 1.1.1
Gunicorn 20.0.4
```
Please check requirements.txt for full dependencies. 

------

## How to use it

### Authentication
Users are required to be authenticated before being allowed to upload images. Unauthenticated accesses are redirected to log in page. 

User should provided an username during registration, which should be uniquely identifiable. Users are required to provide a password of at least 6 characters. Validation on both username and password are performed on server end. User will be redirected to login page upon successful registration. 


### Profile view
Users are redirected to profile upon successful login. The profile view contains an image uploads form and a gallery of thumbnails of uploaded images. Users can select an image file and click on upload button to add a new image. In the gallery section, only images uploaded by the user should be visible, and by clicking on the thumbnails, the user will be redirected to a page with the original image and processed one. 

### API Interface

This application exposes two endpoints below for testing purposes.   
  * api/register: this endpoint accepts HTTP POST requests to register a user. In this requst, there should be a string parameter named username and password. This endpoint will returns login HTML view upon successful registration. 
  * api/upload: this endpoint accepts HTTP POST requests to add image to user gallery. This request should include a string parameter named username, a string parameter named password, a file parameter named file. The enctype property of this request should be set to multipart/form-data. 

------

## Application Architectures


## Assumption and Error Handling


### Error code used by this application

### Error


### Assumption
* image format
* image size
* TPS limit
* 