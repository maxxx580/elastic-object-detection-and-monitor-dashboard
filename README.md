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
Users are required to be authenticated before being allowed to upload images. Unauthenticated accesses are redirected to log in page. 

User should provided an username during registration, which should be uniquely identifiable. Users are required to provide a password of at least 6 characters. Validation on both username and password are performed on server end. User will be redirected to login page upon successful registration. 


### Profile view
Users are redirected to profile upon successful login. The profile view contains an image uploads form and a gallery of thumbnails of uploaded images. Users can select an image file and click on upload button to add a new image. In the gallery section, only images uploaded by the user should be visible, and by clicking on the thumbnails, the user will be redirected to a page with the original image and processed one. 

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
  * response
    ~~~
    {
      success: true
    }

    {
      success: false,
      message: "error message"
    }
    ~~~


## Application Architectures
[![2331581530664.jpg](https://i.postimg.cc/nzJyF6X2/2331581530664.jpg)](https://postimg.cc/zLxtp2SH)   



## Error Handling

* 404 Not Found
* 403 Forbidden
* 401 Unauthorized 
* 400 Bad Request

## Assumption
* Image Format: this application only accept format accepted by open cv framework. The format should be explictly identified as file extension. 
* Image Size: the expected image size is less than 3MB. Larger image will results in degrading performance. 
* TPS Limit: the single host is expected to process 1 transaction per second. 
  