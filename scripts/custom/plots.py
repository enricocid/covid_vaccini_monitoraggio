from datetime import datetime
from glob import glob
from re import findall

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# see: https://personal.sron.nl/~pault/
palette = ["#EE7733", "#0077BB", "#33BBEE", "#EE3377", "#CC3311", "#009988", "#BBBBBB"]


def apply_plot_treatment():
    plt.style.use("seaborn-dark")
    mpl.rcParams["lines.linewidth"] = 1.5
    mpl.rcParams["lines.markersize"] = 3
    mpl.rcParams["lines.marker"] = "o"
    mpl.rcParams["legend.labelspacing"] = 0.25
    mpl.rcParams["legend.borderaxespad"] = 0.25
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=palette)


def get_df_assoluti():
    # dati ISS
    df_assoluti = pd.read_excel("../dati/dati_ISS_complessivi.xlsx", sheet_name="dati epidemiologici")
    df_pop = pd.read_excel("../dati/dati_ISS_complessivi.xlsx", sheet_name="popolazioni")
    df_assoluti = df_assoluti[df_assoluti["data"] > "2021-07-28"]
    df_pop = df_pop[df_pop["data"] > "2021-07-28"]
    return df_assoluti, df_pop


def list_xlsx():
    # lista gli xlsx
    files = np.sort(glob("../dati/data_iss_età_*.xlsx"))
    cut_date = pd.to_datetime("2021-07-28")
    filtered = filter(lambda data: date_from_xlsx_path(data) > cut_date, files)
    return list(filtered)


def date_from_xlsx_path(xlsx_path):
    date_ = findall(r"\d+-\d+-\d+", xlsx_path)[0]
    return datetime.strptime(date_, "%Y-%m-%d")


def get_xticks_labels(reports_dates=None, full=False):
    if reports_dates is None:
        df_assoluti = pd.read_excel("../dati/dati_ISS_complessivi.xlsx", sheet_name="dati epidemiologici")
        df_assoluti = df_assoluti[df_assoluti["data"] > "2021-07-28"]
        reports_dates = pd.to_datetime(df_assoluti["data"])
    if full:
        reports_dates.sort_values(inplace=True)
        sel_dates = reports_dates[0::3]
        labels = [t.strftime("%d\n%b") for t in sel_dates]
        ticks = np.arange(0, len(reports_dates), 3)
    else:
        ticks = set([x.strftime("%Y-%m-01") for x in reports_dates])
        ticks = sorted(ticks)
        labels = [pd.to_datetime(t).strftime("%b\n%Y")
                  if (i == 1 or pd.to_datetime(t).strftime("%m") == "01") or full
                  else pd.to_datetime(t).strftime("%b")
                  for i, t in enumerate(ticks)]
        labels[0] = ""
    labels = list(map(str.title, labels))
    return ticks, labels


def get_yticks_labels(data):
    # Ricava labels y in base al valore minimo
    # della serie di dati considerata
    ymin = round(data.min()-5, -1)
    yticks = np.arange(ymin, 101, 10)
    ylabels = [f"{tick:.0f}%" for tick in yticks]
    return ymin, yticks, ylabels
