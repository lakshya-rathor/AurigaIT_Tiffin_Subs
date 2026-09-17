Problem Statement
A home-style tiffin (lunch delivery) service. Customers subscribe to a monthly plan and get lunch delivered every weekday. Life happens — they pause for a few days (travel, festivals) and shouldn’t be charged for paused days. At month-end the owner needs each customer’s bill: the plan price pro-rated for the days actually delivered. Customers are looked up by phone, and the owner wants to see who’s active versus paused.
Build the tiffin owner something so every customer is billed only for the days they were actually served.
(Build it for any tiffin service. Get subscribe, pause/resume and the pro-rated bill right first, then the lookups.)


# AurigaIT Tiffin Subscription System

A Django-based Tiffin Subscription Management System developed for managing customers, subscriptions, billing, and subscription pause/resume operations from an admin interface.

## Features

- Customer management
- Customer details and registration
- Tiffin subscription management
- Subscription activation
- Subscription pause functionality
- Subscription resume functionality
- Bill generation
- Admin dashboard
- Django-based backend and web interface
- SQLite database for development

## Technology Stack

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite
- Git & GitHub

## Project Structure

```text
AurigaIT_Tiffin_Subs/
│
├── manage.py
├── README.md
├── REASONING.md
├── AI_LOGS.md
│
├── tiffin_manager/
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── ...
│
├── templates/
│   └── ...
│
└── ...


Requirements
Python 3.x
pip
Django
Git
