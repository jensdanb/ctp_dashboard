# Capable-To-Promise Inventory Model

(Work in progress)

This project was borne out of some frustrations working logistics and responding to purchase orders while restricted by the ERP System's Available-To-Promise (ATP) function. Surely I could do this better! Well... easier said than done. 

Capable-To-Promise (CTP) is an extension of Available-To-Promise (ATP). 
ATP is a automatically calculated by most modern MRP and ERP systems in production logistics. It follows from the projected inventory in a planned period, where the projected inventory on any date is the sum [starting inventory] + [planned incoming] - [planned outgoing] inventory between now and that date. Planned outgoing and planned outgoing are usually in the form of sales orders and production orders. This plan may show an inventory of 100 units  on day 10, but if there is already a sales order for 40 units to customer A on day 11; then the amount that can be promised when customer B makes a purchase request for day 10 is only 60. This is what ATP handles; ATP for each date equals the smallest *future* inventory from that date forward. An MRP system enforcing the rule 'ATP >= 0' will not allow sales personnel to confirm a new order larger than the ATP for that same date, thus preventing 'double-booking'. 

This is a good feature, however; the problem must still be solved that customer B wants his order confirmed and fulfilled, the sooner the better. Should order confirmation date be set to a later date where there is enough ATP? Should the sales employee insert a production order in the ERP system, so that ATP is sufficient and the order can be confirmed? Or ask Production department to insert the production order (rearrange their production schedule if needed) and ask the customer to await response until that process is finished? The latter is the safest option, but can be time-consuming and for routine orders may be unneccesary. 
new_direction.angle
Extending ATP to CTP aims to aid in this process by letting the fulfilling actor (Production) define a curve of quantity-time combinations that the intermediary can promise from them without having to ask and discuss every time. A certain production capability is defined (lead time, throughput rate, constraints) by Production which forms a curve. Independently, the capability curve is a very simple mathematical graph, often a straight line with some delay and cutoff. However, it must be combined with pending production and sales orders to produce a current CTP curve that is reliable. With a reliable, always up to date CTP curve and the new rule 'CTP >= 0', sales orders can be immediately confirmed within the CTP curve because Production has already promised that they have the capability to fulfill that level. 

In addition to the improvement in information flow, the independent Capability curve can be cost analysed. It is made up of components (safety stock, surplus capacity, ...) that have yearly costs which can be calculated. With good sales forecasting data, the expected number of orders that are outside (too large on too short notice) a given capability curve can also be calculated. Thus one can analyze cost reductions, like reducing capacity, against the expected associated costs to lost or delayed sales, to inform decisions on whether capability components should be increased, reduced or maintainted. 

An SQL inventory database is made for testing & example purposes. 

A simple example: ![CTP_1](https://user-images.githubusercontent.com/56897399/215297919-00bb72d1-718a-4aee-93e2-6b3f5af06016.png)
