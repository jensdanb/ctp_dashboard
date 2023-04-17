# Capable-To-Promise Inventory Model

## Update! The app is now live at http://194.195.241.8:10101/ctp
Still very much unfinished. The web app has only a few of the features, and the server will be moved to a proper secured https address. But it works, you can now play with it in your browser; no install required.  

This is an app for projecting inventory in a supply chain and demonstrating the use of Capable-To-Promise compared to Available-To-Promise. For background on those two logistics concepts, see [Concept.md](https://github.com/jensdanb/ctp_dashboard/blob/master/Concept.md). At the moment, only 2D projections (quantity vs. time) are implemented. In the future, 3D projections (probability of having a certain quantity at a certain time, based on forecast) may be implemented. It was made for illustrating the logistics concept of Capable-To-Promise as an extension of Available-To-Promise, and for personal practice with Python, data science and web technologies. 

A user interface (work in progress) is made with the H2O Wave framework. As of 03 April 2023 the web app looks like this: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/232503928-e8cc57bf-c325-4bb5-8553-36a3407818b8.png)



This project was borne out of some frustrations working logistics and responding to purchase orders while restricted by the ERP System's Available-To-Promise (ATP) function. Surely I could do this better! Well... easier said than done. 


# Code implementation
If the only goal was to demonstrate CTP, I should probably have downloaded an Open Source ERP system, such as Odoo, but I also have a goal of learning SQL and improving my Python skills, so decided to build from scratch. An SQL database is made to model a 1-1 supply chain for a product. A product can have multiple stockpoints, representing the different stages between raw material and delivered end product, for example "raw material","finished goods" and "customer's inventory". Routes are defined between stockpoints, and transfers are handled in two steps: A MoveRequest, and then one or more MoveOrders that fulfill the request. 'Move' is used instead of 'Sales' because the system handles internal and external transfers the same way, and instead of 'Transaction' or 'Transfer' to make clear that it handles physical movement, not payments etc. 

Projections can be made for any stockpoint, generating a Pandas dataframe and a corresponding MatplotLib plot. Work in progress: Forecasting probability of stockout as the probability that new sales requests exceed the current CTP curve. 

# Webapp 
A user interface is now implemented with the H2O Wave framework. For the moment, it is locked to a premade stockpoint, but it is now possible to generate plots in GUI, with selectable and adjustable parameters. Both MatplotLib (legacy) and H2O plotting engines are supported. 
