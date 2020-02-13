# ece1779-a1

## Overview
This project is a python-based web application that allow users to upload images to server and performs object detection on the image. This application is deployed by gunicorn on a single EC2 host and set to run on port 5000. 

## Group
* Hongyu Liu 1005851295   
* Ran Wang 1006126951   
* Zixiang Ma 1005597285  

## Quick Start

### Access to AWS EC2 instance

### Start Server
To start the server on local host for dev purposes, execute the command below at project root directory
```
bash run.sh
```
To start the deployed server on EC2, executa the start up scritp at Desktop directory with command below. 
```
~/Desktop/$ bash start.sh
```

## Major Dependencies
```
Python 3.7
Flaks 1.1.1
Gunicorn 20.0.4
``` 

## Web interface

### Authentication view

![Log in page](documentation/figures/Screen&#32;Shot&#32;2020-02-12&#32;at&#32;10.38.37&#32;PM.png)  
Users are required to be authenticated before being allowed to upload images. Unauthenticated accesses are redirected to log in page. 
![Registration page](documentation/figures/Screen&#32;Shot&#32;2020-02-12&#32;at&#32;10.38.19&#32;PM.png)  
User should provided an username during registration, which should be uniquely identifiable. Users are required to provide a password of at least 6 characters. Validation on both username and password are performed on server end. User will be redirected to login page upon successful registration. 


### Profile view
![profile page](documentation/figures/Screen&#32;Shot&#32;2020-02-12&#32;at&#32;10.39.15&#32;PM.png)  
Users are redirected to profile upon successful login. The profile view contains an image uploads form and a gallery of thumbnails of uploaded images. Users can select an image file and click on upload button to add a new image. In the gallery section, only images uploaded by the user should be visible. 

### Image view

![image page](documentation/figures/Screen&#32;Shot&#32;2020-02-12&#32;at&#32;10.39.56&#32;PM.png)  
By clicking on the thumbnails, the user will be redirected to the image page with the original image and processed one. The top one is the original image user uploaded and the bottom one is processed by object detection modules. 

## API Interface

This application exposes two endpoints below for testing purposes.   
  ### Registration
  this endpoint accepts HTTP POST requests to register a user. In this requst, there should be a string parameter named username and password. This endpoint will returns login HTML view with code 201 upon successful registration. 

  * Request URL: http://host/api/register    
  * HTTP method: POST    
  * Request parameters  
    * username - string 
    * password - string
  * Success Respose: HTML login view with status code 201

  ### Image
  
  this endpoint accepts HTTP POST requests to add image to user's gallery. This request should include a string parameter named username, a string parameter named password, a file parameter named file. The enctype property of this request should be set to multipart/form-data.    
  * Request URL: http://host/api/upload
  * HTTP method: POST
  * Request parameters
    * username - string
    * password - string
    * file - file
  * response - JSON
    ~~~
    {
      success: true
    }

    {
      success: false,
      message: "error message"
    }
    ~~~

## System Architectures
Two database table are used in this application. the user table is meant to store users' credential information. The image table stores records of images uploaded and it has a foreign key connecting to the user table. 
![DB ER](documentation/figures/2331581530664_.jpg)    



## Error Handling

* 404 Not Found
* 403 Forbidden
* 401 Unauthorized 
* 400 Bad Request

## Assumption
* Image Format: this application only accept format accepted by open cv framework. The format should be explictly identified as file extension. 
* Image Size: the expected image size is less than 3MB. Larger image will results in degrading performance. 
  