# Item-Catalog
Create an item catalog for adding editing and removing items from a database.

### How to Run
# Running the code
1. Download the zip file
2. Install Vagrant And VirtualBox
3. Unzip and place the ItemCatalog folder in your Vagrant directory
4. Launch Vagrant
```
$ Vagrant up
```
5. Login to Vagrant
```
$ Vagrant ssh
```
6. Change directory to `/vagrant/ItemCatalog`
```
$ Cd /vagrant/ItemCatalog
```
7. Initialize the database
```
$ Python database_setup.py
```
8. Populate the database with some initial data
```
$ Python populate_database.py
```
9. Launch application
```
$ Python application.py
```
10. Open the browser and go to http://localhost:8000

### JSON endpoints
#### Returns JSON of all items

```
/items.json
```

#Technology used
VirtualBox
Vagrant
Python(2.7.9)
HTML5
CSS3
OAUTH2