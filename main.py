import math

from QuantConnect import Resolution
from QuantConnect.Algorithm import QCAlgorithm


class TrackedStock:
    """
    Stock that we want to track.

    Attributes:
        ticker (str): The ticker to watch
        targetBuyPrice (float): The intended purchase price
        lastSellingPrice (float): The last price the stock was sold at
        highestPrice (float): The highest price of the stock since it's been purchased
        lowestPrice (float): The lowest price since it's been sold
        lastSellingQuantity (int): The amount sold
    """

    def __init__(self, ticker, buy_price):
        """

        :param str ticker: The stock ticker to watch
        :param float buy_price: The lowest buy price
        """
        self.ticker = ticker
        self.targetBuyPrice = buy_price
        self.lastSellingPrice = 0
        self.highestPrice = self.targetBuyPrice
        self.lowestPrice = self.targetBuyPrice
        self.lastSellingQuantity = 0

    def sell(self, price, quantity):
        """

        :param float price: The price the stock was sold at
        :param int quantity: The amount of stock sold
        :return:
        """
        self.lastSellingPrice = price
        self.lastSellingQuantity = quantity
        self.highestPrice = price
        self.lowestPrice = price

    def update_price(self, trade_bar):
        """
        Update the highest and lowest price of the tracked stock

        :param trade_bar: 
        :return:
        """
        if trade_bar.High > self.highestPrice:
            self.highestPrice = trade_bar.High
        if trade_bar.Low < self.lowestPrice:
            self.lowestPrice = trade_bar.Low

    def get_target_price(self):
        """
        Get the target buy price that is set or if it was sold once the price is 10% above the lowest price

        :return: The target buy price
        """
        if self.lastSellingPrice == 0:
            return self.targetBuyPrice
        return self.lowestPrice * 1.15


class FirstAlpha(QCAlgorithm):
    """
    :attr TrackedStock trackedStocks: List of tracked stocks

    """

    def Initialize(self):
        self.SetStartDate(2019, 1, 1)  # Set Start Date
        self.SetCash(10000)  # Set Strategy Cash

        # set target buy prices
        self.trackedStocks = [TrackedStock("TDOC", 10)]

        self.ba = self.AddEquity("BA", Resolution.Daily)
        self.tdoc = self.AddEquity("TDOC", Resolution.Daily)
        self.microsoft = self.AddEquity("MSFT", Resolution.Daily)
        self.facebook = self.AddEquity("FB", Resolution.Daily)

    def OnData(self, data):
        """OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.
            Arguments:
                data: Slice object keyed by symbol containing the stock data
        """
        for trackedStock in self.trackedStocks:
            stock_bar = data.Bars[trackedStock.ticker]
            trackedStock.update_price(stock_bar)

            # if we don't already have the current let's get some if the price is right
            if not self.Portfolio[
                trackedStock.ticker].Invested and stock_bar.Low > trackedStock.get_target_price():
                self.MarketOrder(trackedStock.ticker,
                                 math.floor((self.Portfolio.Cash / len(self.trackedStocks)) / stock_bar.Open))
                trackedStock.highestPrice = stock_bar.Open
                trackedStock.lowestPrice = stock_bar.Open

            # if we made 20% on our holding let's sell out position. If the stock shaved 30% let's sell as well
            if self.Portfolio[trackedStock.ticker].Invested and ((self.Portfolio[
                trackedStock.ticker].UnrealizedProfitPercent > .2 and stock_bar.Open < .9 * trackedStock.highestPrice) or self.Portfolio[
                trackedStock.ticker].UnrealizedProfitPercent < -.3):
                self.Debug("unrealized profit" + str(self.Portfolio[trackedStock.ticker].UnrealizedProfitPercent))
                self.MarketOrder(trackedStock.ticker, self.Portfolio[trackedStock.ticker].Quantity * -1)
                trackedStock.sell(stock_bar.Open, self.Portfolio[trackedStock.ticker].Quantity)
