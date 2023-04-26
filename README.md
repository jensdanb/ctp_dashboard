# Capable-To-Promise Inventory Model

## Update! The app is now public at http://194.195.241.8:10101
The app is still incomplete and the server is not well secured, but it doesn't contain important data and you can now try it out without installing. If you want to install and run it locally on your machine, instructions are at the bottom of this page. 


## What is this? 

This is an app for managing inventory in a supply chain and demonstrating the Capable-To-Promise (CTP) logistics concept. Explainer on CTP is found here: [Concept.md](https://github.com/jensdanb/ctp_dashboard/blob/master/Concept.md). 


When you open the app in your browser, a database containing two Products is generated for you, and each product has a number of Stockpoints (inventory locations) connected by SupplyRoutes, representing the supply chain. An example (Product A) has the stockpoints Unfinished Goods -> Finished Goods -> Customer Inventory connected by two SupplyRoutes Route 1 and Route 2. 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/234340769-e4e72008-e183-4de3-9510-ccdd5b79fa79.png)


To move goods along a SupplyRoute, a MoveRequest for a certain quantity is first created, then confirmed with one or more MoveOrders to fulfill the requested quantity. Inventory is transferred when the MoveOrder is executed, and at the same time the completion status of the MoveRequest is updated. 

A user interface is made with the H2O Wave framework. 

Use the navigation header in the top right corner to move between pages. The Home page is empty for now. 
On the Database page, you can show the supply chain for a product in both table and graph form. The latter is auto-generated with networkx and pyvis, and passed as raw html to a UI card in the WebApp. You can also show other tables with MoveRequests and MoveOrders from the database, and regenerate a fresh database with the Reset Database button. Editing, adding and removing database content in a more controlled way will be supported here. 

Database page UI status on 25 April 2023: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/234341586-769695ed-3f06-4ad5-a5ff-fd0cd92c9114.png)


The Plotting page is for showing the projected inventory over time in any selected Stockpoint. The Python Pandas library is used to generate tables with daily inventory availability, projected from the pending incoming/outgoing (supply/demand) MoveOrders in the database affecting this stockpoint. In addition to projected inventory, ATP and CTP is also displayed, representing what amount of inventory can be used to respond to new MoveRequests under an ATP or CTP policy. 

Plotting page UI status on 03 April 2023: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/232503928-e8cc57bf-c325-4bb5-8553-36a3407818b8.png)

## Planned features
1: Ability to edit database content in the WebApp UI


2: Testing that branching supply chains (stockpoints with more than one outgoing and one incoming SupplyRoute) work


3: Moving the public server to a better secured server with https and appropriate domain name


4: User accounts with persistent database between sessions, and a login portal for this. 


## Instructions for running this on your own machine

If you want to run the app on your own machine, do the following steps. If you are unfamiliar with any of the steps, search for a recent guide online: None of them are very hard, and the guide will explain them better than I could do here. These instructions are for Linux machines. Details of each step is slightly different for MacOS and more different for Windows, but the general procedure should be roughly the same. 

1: Install Python3 on your computer


2: Use git to clone the project from this url address to a folder on your machine


3: Create and activate a Python Virtual Environment inside the folder you got from git


4: Use python pip to install dependencies by exuting (while still inside the Virtual Environment) the following command: pip install -r requirements.txt


5: Run the app with wave by executing the following command: wave run web_app

