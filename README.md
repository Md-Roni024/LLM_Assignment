## Table of Contents
1. [Overview ](#Overview )
1. [Features](#features)
2. [Tools & Technologies](#technologies)
3. [Project Structure](#project-structure) 
5. [Run & Setup](#Running-the-project)
6. [Schema Design](#Design-Database)
7. [Contributing](#Contributing)
8. [Contact](#Contact)
10. [License](#license)


## Overview

This assignmnet is based on previous 'django_assignmnet'. Here I used Large Language Model(LLM) , OLamma Library named: gemma2:2b for updateing property information and generate a summary for each property. For updateing property description I used existing 'title,rating,room_type,price' and for updateing title I used newly created description along with existing 'title,rating,price,room_type'. After update title ,description parallelly I create a summary for each property based on 'title,description,rating,price,room_type,location,amenities'.




## Features

- Implements Large Language Model(LLM)
- Move hotels data from 'scrapy_database' to 'django_database' by CLI application.
- Update property title and description by using LLM
- Generate summary for each property
- Maintain proper data table realtionship with different property like:(One to Many , Many to Many)
- Apply CRUD operations

## Technologies
- Django
- Python3
- PostgreSQL
- Command Line Interface(CLI)
- Ollama
- Django ORM

 

## Project Structure
```
django_assignment/
│
├── django_assignment/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── myapp/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── management
│   │   └── commands
│   │        └── migrate_data.py
│   │        └── update_property
│   ├── migrations/
│   │   └── __init__.py
│   ├── templates
│   │   └── __hello.html
│   ├── models.py
│   ├── admin.py
│   ├── tests.py
│   ├── apps.py
│   ├── views.py
│   ├── urls.py
├── manage.py
├── .gitignore
└── requirements.txt

```

### Model summary
  ```
  Model Name: gemma2
  Parameters: 2B
  Architecture: gemma2
  ```

### Setup OLlama & gemma2:2b Model
  ```bash
  #For Linux
  curl -fsSL https://ollama.com/install.sh | sh

  #For MacOS | Windows
  Go to this url: https://ollama.com/download 
  Then download and install it
  ```
  After successfuly run & install OLlama, execute foolowing command in terminal , it will start pull gemma2:2b Model in local machine.
  ```bash
  ollama run gemma2:2b
  ```



### Design-Database

- Only Create a database name as bellow, all the table will be created automatically using ORM.
  ```
  CREATE DATABASE django_database;
  ```


## Running-the-project

1. Clone the repository:
   ```bash
   git clone https://github.com/Md-Roni024/LLM_Assignment

   ```

2. Go to the project directory and Create Virtual Environment & activate
    ```bash
    cd LLM_Assignment
    python3 -m venv venv

    #For Linux | MacOS
    source venv/bin/activate

    #For Windows
    venv\Scripts\activate
    ```


3. Install all the dependencies :
   ```bash
   pip install -r requirements.txt
   ```
4. Create a .env file then add variables credentials as bellow:
    ```bash
      HOST=localhost
      PORT=5433
      DB_USER=postgres
      PASSWORD=p@stgress
      SCRAPY_DATABASE=hotel_db
      DJANGO_DATABASE=django_database
    ```


5. Now Migrate the django datbase table

    ```bash
    cd django_assignment

    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
6. Run CLI for migrate data to django database
    ```bash
      python3 manage.py migrate_data
    ```


7. Run CLI for update title, description and create summary
    ```bash
    python3 manage.py update_description
    ```

8. Create super admin by terminal for access sjango admin

   ```bash
    python manage.py createsuperuser
    Username: 'Put Your Username'
    Username: 'Put your password, minimum 8 alphanumeric character'
   ```
9. Run dajango admin
    ```bash
    python3 manage.py runserver
    ```
   Go to this url: http://127.0.0.1:8000/admin/

  

## Contributing
- Contributing is an open invitation for collaboration on the project. You're encouraged to participate by opening issues for bugs or feature requests and submitting pull requests with your improvements or fixes. Your contributions help enhance and grow the project, making it better for everyone.

## Contact

- For any questions or feedback, please reach out to me at roni.cse024@gmail.com. I welcome all inquiries and look forward to hearing from you. Your input is valuable and appreciated!

## Licences
- Distributed under the MIT License. See LICENSE.txt for more information.
