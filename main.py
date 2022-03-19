
from ast import Continue
from datetime import date
import datetime
from functools import total_ordering
import pandas
import plotly.express as px



# Global constants (move to config later)

# The interest it takes to borrow the line of credit
BORROW_INTEREST = 0.0225
DAILY_BORROW_INTEREST = BORROW_INTEREST/365

# How much below the peak before starting the buy sell (too close to the peak and you risk not making profit for too long, too far from the peak you risk missing making transactions)
PERCENT_OFF_PEAK_TO_BUY = 0.03

# How much profit do I want to see on the transaction before selling
TRANSACTION_ROI_SELL_POINT = 0.02

# How much credit you want to risk in this simulation, makes assumption you cash on earnings and don't reinvest them
LINE_OF_CREDIT = 3000

# This is the percentage you earn from dividends on stocks you own
DIVIDENT_YEILD = 0.023


class Transaction:
    def __init__(self, opening_date: date, closing_date: date, buying_value: float, selling_value: float, amount: float) -> None:
        if not isinstance(opening_date, date):
            raise ValueError(f"opening_date must be class datetime.date not {opening_date.__class__}")
        if not isinstance(closing_date, date):
            raise ValueError(f"closing_date must be class datetime.date not {closing_date.__class__}")
        if not (isinstance(buying_value, int) or isinstance(buying_value, float)):
            raise ValueError(f"buying_value must be class int or float not {buying_value.__class__}")
        if not (isinstance(selling_value, int) or isinstance(selling_value, float)):
            raise ValueError(f"selling_value must be class int or float not {selling_value.__class__}")
        if not (isinstance(amount, int) or isinstance(amount, float)):
            raise ValueError(f"amount must be class int or float not {amount.__class__}")
        if opening_date>=closing_date:
            raise ValueError(f"Opening date `{opening_date}` must come stricty before closing date `{closing_date}")

        self.opening_date = opening_date
        self.closing_date = closing_date
        self.buying_value = buying_value
        self.selling_value = selling_value
        self.amount = amount
    

    def __repr__(self):
        return f"Transaction: {self.opening_date} -> {self.closing_date} lasing {(self.closing_date-self.opening_date).days} days. Earning {self.get_profit()} net profit"

    def get_interest(self):
        return (self.closing_date - self.opening_date).days * DAILY_BORROW_INTEREST * self.amount

    def get_profit(self):
        # print(self.selling_value, self.buying_value, (self.selling_value - self.buying_value))
        return (((self.selling_value - self.buying_value)/self.buying_value)*self.amount)-self.get_interest()

    def get_length(self):
        return (self.closing_date-self.opening_date).days

def main():
    df = pandas.read_csv("resources/S_and_P_500_Daily_Historical_Data.csv")[::-1] #[::-1] needed to flip dataset around to oldest to newest
    current_peak = 0
    num_of_transactions = 0
    transactions = []
    list_of_days_in_market = []
    currently_in_transaction = False
    for _,row in df.iterrows():
        current_date = datetime.datetime.strptime(row['Date'], '%m/%d/%Y').date()
        current_stock_value = row['Close/Last'] 
        if current_peak < current_stock_value:
            current_peak = current_stock_value

        if not currently_in_transaction:
            # If not in transaction, wait until we are percent off peak

            list_of_days_in_market.append(None)

            percent_off_peak = 1-(current_stock_value/current_peak)
            if(percent_off_peak>=PERCENT_OFF_PEAK_TO_BUY):
                currently_in_transaction = True
                transaction_buying_date = current_date
                transaction_buying_value = current_stock_value
                # list_of_days_in_market.append(current_date)

        else:
            # if in transaction, wait until values have gone up to sell point for that transaction
            sell_point_for_current_transaction = transaction_buying_value*(1+TRANSACTION_ROI_SELL_POINT)
            
            list_of_days_in_market.append(current_stock_value)

            if current_stock_value > sell_point_for_current_transaction:
                currently_in_transaction = False
                transactions.append(Transaction(transaction_buying_date, current_date, transaction_buying_value, current_stock_value, LINE_OF_CREDIT))
                num_of_transactions += 1


    total_profit = 0
    total_interest = 0
    longest_transaction = transactions[0]
    # most_credit_charged_on_transaction = None
    for transaction in transactions:
        total_profit += transaction.get_profit()
        total_interest += transaction.get_interest()
        if transaction.get_length() > longest_transaction.get_length():
            longest_transaction = transaction
    

    output_line1 =  f"Over 10 years, using a PLoC of {LINE_OF_CREDIT}, "
    output_line1 += f"and buying only when under {PERCENT_OFF_PEAK_TO_BUY*100}% "    
    output_line1 += f"off peak, selling when profit reached {TRANSACTION_ROI_SELL_POINT*100}% ROI of transaction..."
    output_line2 =  f"Total net profit equals ${round(total_profit,2)}, " 
    output_line2 += f"longest single transaction lasted {longest_transaction.get_length()} days" 
    output_line2 += f"(with interest charge of ${round(longest_transaction.get_interest(),2)}) "
    output_line2 += f"and total interest charged was ${round(total_interest,2)}"
    print(output_line1)
    print(output_line2)


    df['in_market'] = list_of_days_in_market
    fig = px.line(df, x="Date", y=["Close/Last", "in_market"], title='S&P 500')
    fig.show()


if __name__ == "__main__":
    main()