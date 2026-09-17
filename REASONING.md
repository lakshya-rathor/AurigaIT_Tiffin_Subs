
---

### `REASONING.md`

Ye file evaluator ko **tumne solution kaise approach kiya** ye batayegi:

```markdown
# Reasoning Behind the Solution

## 1. Problem Understanding

The objective was to develop a Tiffin Subscription Management System that can simplify the management of customers and their tiffin subscriptions.

The initial implementation focuses on the administrative side of the system. The admin can manage customers, subscriptions, billing, and subscription pause/resume operations.

## 2. Technology Selection

Django was selected as the primary framework because it provides:

- A structured backend framework
- Built-in URL routing
- Template support
- ORM for database operations
- Built-in authentication and administration
- Rapid development capabilities

SQLite was used during development because it is simple to configure and is suitable for a local development environment.

HTML, CSS and JavaScript were used for the frontend interface.

## 3. Development Approach

The project was developed incrementally.

The main development steps were:

1. Create the Python virtual environment.
2. Create the Django project.
3. Configure Django settings.
4. Create the required application functionality.
5. Design customer-related pages.
6. Implement subscription operations.
7. Implement pause and resume functionality.
8. Implement bill generation.
9. Create the admin dashboard.
10. Test the application using the Django development server.
11. Track the source code using Git.
12. Push the project to a public GitHub repository.

## 4. Subscription Logic

The system treats the subscription as an entity associated with a customer.

The major subscription states considered during development are:

- Active
- Paused
- Resumed

The pause and resume operations are handled through dedicated application views and forms.

## 5. Billing Logic

The billing functionality was separated from general customer management so that bills can be generated using the customer's subscription-related information.

This makes it possible to extend the billing module later with:

- Different meal plans
- Monthly billing
- Discounts
- Payment status
- Online payments

## 6. Testing

The application was tested locally using Django's development server.

Basic testing included:

- Starting the Django server.
- Opening the application in a browser.
- Testing customer-related forms.
- Testing subscription operations.
- Testing pause and resume operations.
- Testing bill generation.
- Checking Django configuration using:

```bash
python manage.py check
