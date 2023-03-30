# Capable-To-Promise Inventory Model

This is an app for projecting inventory in a supply chain. At the moment, only 2D projections (quantity vs. time) are implemented. In the future, 3D projections (probability of having a certain quantity at a certain time, based on forecast) may be implemented. It was made for illustrating the logistics concept of Capable-To-Promise as an extension of Available-To-Promise, and for personal practice with Python, data science and web technologies. 

A user interface (work in progress) is made with the H2O Wave framework. Currently the web app looks like this: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/228826684-beda9b63-697e-4427-9165-4ea42c024f6c.png)


This project was borne out of some frustrations working logistics and responding to purchase orders while restricted by the ERP System's Available-To-Promise (ATP) function. Surely I could do this better! Well... easier said than done. 

### Capable-To-Promise (CTP) is an extension of ATP. For the uninitiated, an explanation of ATP: 
ATP is a automatically calculated by most modern MRP and ERP systems in production logistics. It follows from the projected inventory in a planned period, where the projected inventory on any date is the sum [starting inventory] + [planned incoming] - [planned outgoing] inventory between now and that date. Planned demand and planned supply are usually in the form of sales orders and production orders. This plan may project an inventory of 100 units to be in stock on day 10, but if there is already a sales order for 40 units to customer A on day 11, then the amount available for a potential new customer B on day 10 is only 60. ATP for any date equals the smallest *future* projected inventory level from that date forward. An MRP system enforcing the rule 'ATP >= 0' will not allow sales personnel to confirm a new order with a delivery date where the order quantity is larger than ATP for that date, thus preventing 'double-booking'. 

For example, here is projected inventory for a product with four pending sales (red bars) and two pending replenishments (blue bars) over the next 20 days: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/228826910-2772e7b1-a27c-492c-b894-878092e6c453.png)


Now let's overlay ATP (the stronger green) to see the difference: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/228661071-a866f3b5-8aff-43cb-87ac-087a61908aba.png)


This is a good feature, however; the problem must still be solved that customer B wants his order confirmed and fulfilled, the sooner the better. Should order confirmation date be set to a later date where there is enough ATP? Should the sales employee insert a production order in the ERP system, so that ATP is sufficient and the order can be confirmed? Or ask Production department to insert the production order (rearrange their production schedule if needed) and ask the customer to await response until that process is finished? The latter is the safest option, but can be time-consuming and for routine orders may be unneccesary. 


## This is where Capable-To-Promise (CTP) comes in. 
In short, CTP aims to solve this by letting Production define a general capability that they can promise, which takes the form of a volume/time curve. Sales responsible can then confirm customer orders without having to consult production, as long as it is within the promised capability. 

The tricky parts are 
1) To define this capability in the first place. Usually it is made by answering a set of questions; about lead (response) time, throughput capacity, and constraints (for example if max throughput can only be maintained for a number of days, or if access to input materials is constrained. These answers must be made into a volume/time function that Production can promise to keep. 
2) Combining the general capability curve with the pending sales, purchases and productions, into a specific and up-to-date curve that Sales can use to Confirm/Postpone/Decline new incoming purchase orders. 

In addition to the improvement in information flow, the independent Capability curve can be cost analysed. It is made up of components (safety stock, surplus capacity, ...) that have yearly costs which can be calculated. With good sales forecasting data, the expected number of orders that are outside (too large on too short notice) a given capability curve can also be calculated. Thus one can analyze cost reductions, like reducing capacity, against the expected associated costs to lost or delayed sales, to inform decisions on whether capability components should be increased, reduced or maintainted. 

A simple linear CTP can be seen in the image below. In this case there is no uncommitted capacity until the 15th day, it is already busy with the planned production deliveries (blue bars), and therefore CTP=ATP for most of the period: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/228661921-e2788c67-3889-4486-b8f3-6964bc7cb5f8.png)

However, if we look at a longer period, for example 33 days instead of 20, we start to see the difference: 
![Screenshot_20230329_222921](https://user-images.githubusercontent.com/56897399/228662592-36bc6ad3-a15f-4f93-9c4c-693a989c5328.png)
Using CTP instead of ATP gives sales department the ability to give "common sense" order confirmations for dates outside the current plan period. Especially useful for large orders that may be placed half a year in advance. Working in an ATP environment, we had to discuss with production every time, make up fake production plans and edit them later, just to get those orders into the system.  

# Code implementation
If the only goal was to demonstrate CTP, I should probably have downloaded an Open Source ERP system, such as Odoo, but I also have a goal of learning SQL and improving my Python skills, so decided to build from scratch. An SQL database is made to model a 1-1 supply chain for a product. A product can have multiple stockpoints, representing the different stages between raw material and delivered end product, for example "raw material","finished goods" and "customer's inventory". Routes are defined between stockpoints, and transfers are handled in two steps: A MoveRequest, and then one or more MoveOrders that fulfill the request. 'Move' is used instead of 'Sales' because the system handles internal and external transfers the same way, and instead of 'Transaction' or 'Transfer' to make clear that it handles physical movement, not payments etc. 

Projections can be made for any stockpoint, generating a Pandas dataframe and a corresponding MatplotLib plot. Work in progress: Forecasting probability of stockout as the probability that new sales requests exceed the current CTP curve. 

# Webapp 
A user interface is now implemented with the H2O Wave framework. For the moment, it is locked to a premade stockpoint, but it is now possible to generate plots in GUI, with selectable and adjustable parameters. Both MatplotLib (legacy) and H2O plotting engines are supported. 
