# Capable-To-Promise Inventory Model

(Work in progress)

Capable-To-Promise (CTP) is an extension of Available-To-Promise (ATP). 
ATP is a value automatically calculated by most modern MRP and ERP systems in production logistics. It follows from the projected inventory in a planned period, where the projected inventory on any date is the sum of starting inventory plus planned incoming minus planned outgoing inventory, usually in the form of production orders and sales orders. The plan may show an inventory of 100 units on Monday, but these cannot all be sold then if there is already a sales order for 50 units on Tuesday. ATP accounts for this, as it is always equal to the smallest future inventory. An MRP system enforcing the rule 'ATP >= 0' will not allow sales personnel to confirm a new order larger than the ATP for that same date, and 'double-booking' is prevented. 

However, the problem must still be solved that the customer wants his order confirmed and fulfilled, preferably on time. Should order confirmation date be set to a later date where there is enough ATP? Should the sales employee insert a production order, so that ATP is sufficient and the order can be confirmed as soon as possible? Or ask Production department to insert a new production order (and rearrange their production schedule) and ask the customer to await response until discussion and rescheduling is finished? The latter sounds most reasonable, but can be time-consuming and for routine orders unneccesary. 

Extending ATP to CTP aims to aid in this process by letting the fulfilling actor (Production) define a curve of quantity-time combinations that the intermediary can promise from them without having to ask and discuss every time. A certain production capability is defined (lead time, throughput rate, constraints) by Production which forms a curve. Independently, the capability curve is a very simple mathematical graph, often a straight line with some delay and cutoff. However, it must be combined with pending production and sales orders to produce a current CTP curve that is reliable. With a reliable, always up to date CTP curve and the new rule 'CTP >= 0', sales orders can be immediately confirmed within the CTP curve because Production has already promised that they have the capability to fulfill that level. 

In addition to the improvement in information flow, the independent Capability curve can be cost analysed. It is made up of components (safety stock, surplus capacity, ...) that have yearly costs which can be calculated. With good sales forecasting data, the expected number of orders that are outside (too large on too short notice) a given capability curve can also be calculated. Thus one can analyze cost reductions, like reducing capacity, against the expected associated costs to lost or delayed sales, to inform decisions on whether capability components should be increased, reduced or maintainted. 

An SQL inventory database is made for testing & example purposes. 

A simple example: ![CTP_1](https://user-images.githubusercontent.com/56897399/215297919-00bb72d1-718a-4aee-93e2-6b3f5af06016.png)
