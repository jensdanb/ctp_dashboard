from databasing.database_model import *
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

""" Parent class: """


class StockProjection:
    def __init__(self, session: Session, stockpoint: StockPoint, plot_period=24):

        if not plot_period in range(3, 366):
            raise AttributeError('plot_period must be an integer between 3 and 365')

        # start and end of projection
        self.start_date = date.today()
        self.duration = 365
        self.final_date = self.start_date + timedelta(days=self.duration)
        self.dates_range = pd.date_range(self.start_date, self.final_date)

        # basic stockpoint attributes
        self.stockpoint_id = stockpoint.id
        self.stockpoint_name = stockpoint.name
        self.starting_stock = stockpoint.current_stock

        # known events in scope:
        planned_receipts = order_filter(session, stockpoint, self.start_date, self.final_date,
                                        incoming=True, outgoing=False, completed_or_pending='pending')
        planned_sends = order_filter(session, stockpoint, self.start_date, self.final_date,
                                     incoming=False, outgoing=True, completed_or_pending='pending')
        self.included_moves = [order.__dict__ for order in planned_sends + planned_receipts]

        # Main projection dataframe
        self.df = self.project_inventory(planned_receipts, planned_sends)


    def __repr__(self):
        return f"Inventory projection for stockpoint {self.stockpoint_id} ({self.stockpoint_name + ' for selected product'}), from {self.start_date}."

    def project_inventory(self, planned_receipts, planned_sends):
        df = pd.DataFrame([[0 for col in range(2)] for row in range(self.duration + 1)], index=self.dates_range,
                          columns=["demand", "supply"])

        for receipt in planned_receipts:
            df.loc[receipt.order_date.isoformat(), ["supply"]] += receipt.quantity
        for send in planned_sends:
            df.loc[send.order_date.isoformat(), ["demand"]] -= send.quantity
        inventory = np.cumsum(df["supply"]) + np.cumsum(df["demand"])

        df["inventory"] = np.add(inventory, self.starting_stock)
        return df


def minimum_future(values: list):
    return [min(values[i:]) for i in range(len(values))]


class ProjectionATP(StockProjection):
    def __init__(self, session: Session, stockpoint: StockPoint, plot_period=24):
        super().__init__(session, stockpoint, plot_period)
        self.df["ATP"] = minimum_future(self.df["inventory"])
        self.plot = self.make_plot(plot_period)

    def make_plot(self, duration: int):
        plot_window = self.df.loc[self.start_date:self.start_date + timedelta(days=duration)].copy()

        fig, (ax1, ax2) = plt.subplots(2, sharex='all', sharey='all', figsize=(16, 12))
        plt.xlabel("Day")
        plt.ylabel("Quantity")

        # Subplot 1:
        ax1.bar(plot_window.index, plot_window['demand'], label='Demand', color='red', width=0.2)
        ax1.bar(plot_window.index, plot_window['supply'], label='Supply', color='green', width=0.2)
        ax1.plot(plot_window.index, plot_window['inventory'], label='Inventory', color='blue', linewidth=3, marker='o',
                 markersize=5)
        # plot_window['inventory'].plot(ax=ax1, color='blue', linewidth=3, marker='o', markersize=5)
        ax1.fill_between(plot_window.index, 0, plot_window['inventory'], alpha=0.2)

        # Subplot 2:
        ax2.plot(plot_window['inventory'], label='Inventory', color='blue', linewidth=3, marker='o', markersize=5)
        ax2.plot(plot_window['ATP'], label='ATP', color='orange', linewidth=3, marker='o', markersize=5)
        ax2.fill_between(plot_window.index, 0, plot_window['inventory'], alpha=0.2)
        ax2.fill_between(plot_window.index, 0, plot_window['ATP'], alpha=0.2)

        for axis in [ax1, ax2]:
            axis.grid(visible=True, axis='y')
            axis.legend()
            axis.set_ylabel('Quantity')
            axis.set_xlabel('Day')

        fig.suptitle(repr(self), fontsize=16)
        return plt


def potential_capacity(df: pd.DataFrame, route: SupplyRoute) -> pd.Series:
    column = pd.Series(data=[route.capacity] * len(df.index), index=df.index)
    column[:route.lead_time] = [0] * route.lead_time
    column = np.cumsum(column)
    return column


class ProjectionCTP(StockProjection):
    def __init__(self, session: Session, stockpoint: StockPoint, plot_period=24):
        super().__init__(session, stockpoint, plot_period)
        self.df["ATP"] = minimum_future(self.df["inventory"])
        incoming_routes = get_incoming_routes(session, stockpoint)

        if not incoming_routes:
            self.df['CTP'] = self.df["ATP"]
        elif len(incoming_routes) != 1:
            raise NotImplementedError('Can only project ctp from SINGLE incoming route.')
        else:
            for route in incoming_routes:
                self.project_ctp(route)
        self.plot = self.make_plot(plot_period)

    def project_ctp(self, route: SupplyRoute):
        receiver = route.receiver
        if not self.stockpoint_name == receiver.name:
            raise NotImplementedError('Can only project ctp from incoming route.')
        else:
            self.df['cum_supply'] = np.cumsum(self.df['supply'])
            self.df['cum_capacity'] = potential_capacity(self.df, route)
            self.df['unused_capacity'] = self.df[['cum_supply', 'cum_capacity']].max(axis=1) - self.df['cum_supply']

            # Purge premature "unused capacity" which is in fact committed to a later delivery.
            i = 0
            for unused_capacity in self.df['unused_capacity'][::-1]:
                if unused_capacity <= 0:
                    self.df['unused_capacity'].iloc[:self.duration + 1 - i] = 0
                    break
                i += 1

            self.df["CTP"] = self.df["ATP"] + self.df['unused_capacity']
            self.df["CTP"] = self.df[['ATP', 'CTP']].max(axis=1)
            self.df.drop(columns=['cum_supply', 'cum_capacity', 'unused_capacity'], inplace=True)

    def make_plot(self, duration: int):

        plot_window = self.df.loc[self.start_date:self.start_date + timedelta(days=duration)].copy()

        fig, (ax1, ax2, ax3) = plt.subplots(3, sharex='all', sharey='all', figsize=(16, 12))
        plt.xlabel("Day")
        plt.ylabel("Quantity")

        # Subplot 1:
        ax1.bar(plot_window.index, plot_window['demand'], label='Demand', color='red', width=0.2)
        ax1.bar(plot_window.index, plot_window['supply'], label='Supply', color='green', width=0.2)
        ax1.plot(plot_window.index, plot_window['inventory'], label='Inventory', color='blue', linewidth=3, marker='o',
                 markersize=5)
        # plot_window['inventory'].plot(ax=ax1, color='blue', linewidth=3, marker='o', markersize=5)
        ax1.fill_between(plot_window.index, 0, plot_window['inventory'], alpha=0.2)

        # Subplot 2:
        ax2.plot(plot_window['inventory'], label='Inventory', color='blue', linewidth=3, marker='o', markersize=5)
        ax2.plot(plot_window['ATP'], label='ATP', color='orange', linewidth=3, marker='o', markersize=5)
        ax2.fill_between(plot_window.index, 0, plot_window['inventory'], alpha=0.2)
        ax2.fill_between(plot_window.index, 0, plot_window['ATP'], alpha=0.2)

        if any("CTP" in key for key in self.df.keys()):
            ctp_name = self.df.keys()[-1]
            ax3.plot(plot_window['ATP'], label='ATP', color='orange', linewidth=3, marker='o', markersize=5)
            ax3.plot(plot_window[ctp_name], label=ctp_name, color='cyan', linewidth=3, marker='o', markersize=5)
            ax3.fill_between(plot_window.index, 0, plot_window[ctp_name], alpha=0.2)
            ax3.fill_between(plot_window.index, 0, plot_window['ATP'], alpha=0.2)

        for axis in [ax1, ax2, ax3]:
            axis.grid(visible=True, axis='y')
            axis.legend()
            axis.set_ylabel('Quantity')
            axis.set_xlabel('Day')

        fig.suptitle(self.__repr__(), fontsize=16)
        return plt