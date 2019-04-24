# Web of Things Sample Application
This application aims to communicate with a Web of Things network to control devices. It has been developed as a Django application.

## Installation
To install, run the `install.sh` script on a Debian based Linux distribution.

## Apps
The application consists of a number of Django "apps", each which performs a piece of functionality
* accounts: Allows the user to log in and out of the site. Templates include the pages to perform this functionality
* pages: No dynamic content occurs here, they only render static pages
* things: Any pages pertaining to a Thing, including:
  * Showing all things
  * Performing interactions
  * Updating settings

## Templates
All templates are extended from `templates/base.html`, which defines a `content` block. In the "things" app, all pages are extended from one of two templates. The first is `templates/things/list.html` which is used for the thing list. The rest are extended from `templates/things/single.html`, which places information such as the name and description. In doing so, another block `thing_content` is defined for pages to implement.

The generic exception page is overridden to use the base template. This is defined in `templates/exceptions/exception.html`.

## Configuration
All configuration is performed in `wotclient/settings.py` and must be set before installation. Parameters include:
* THING_DIRECTORY_HOST: IP address/hostname of the thing directory
* THING_DIRECTORY_KEY: API key (if required) to access the thing directory
