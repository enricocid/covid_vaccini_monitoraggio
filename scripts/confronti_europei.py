# -*- coding: utf-8 -*-

import locale
from os import chdir, path

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text
from sklearn.metrics import r2_score

from custom.plots import aggiorna_ascissa
from custom.watermarks import add_watermark

paesi_abitanti_eu = {"Austria": 8.917, "Belgium": 11.56, "Bulgaria": 6.927,
                     "Cyprus": 1.207, "Croatia": 4.047, "Denmark": 5.831,
                     "Estonia": 1.331, "Finland": 5.531, "France": 67.39,
                     "Germany": 83.24, "Greece": 10.27, "Ireland": 4.995,
                     "Italy": 59.55, "Latvia": 1.902, "Lithuania": 2.795,
                     "Luxembourg": 0.632275, "Malta": 0.525285, "Netherlands": 17.44,
                     "Poland": 37.95, "Portugal": 10.31, "Czechia": 10.7,
                     "Romania": 19.29, "Slovakia": 5.549, "Slovenia": 2.1,
                     "Spain": 47.35, "Sweden": 10.35, "Hungary": 9.75}

paesi_eu_ita = ["Austria", "Belgio", "Bulgaria", "Cipro", "Croazia", "Danimarca",
                "Estonia", "Finlandia", "Francia", "Germania", "Grecia", "Irlanda",
                "Italia", "Lettonia", "Lituania", "Lussemburgo", "Malta", "Olanda",
                "Polonia", "Portogallo", "Repubblica Ceca", "Romania", "Slovacchia",
                "Slovenia", "Spagna", "Svezia", "Ungheria"]


# Importa dati vaccini e dati epidemiologici
def import_vaccines_data():
    """ Recupera dati sui vaccini da Our World in Data"""

    url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"  
    df_vacc = pd.read_csv(url)
    df_vacc = df_vacc.fillna(method="ffill")
    return df_vacc


def get_vaccine_data(country, df_vacc):
    """ Recupera dati vaccini per paese """

    df_vacc_country = df_vacc[df_vacc["location"] == country].iloc[2:, :]

    date = pd.to_datetime(df_vacc_country["date"])
    vacc1 = np.array(df_vacc_country["people_vaccinated_per_hundred"])
    vacc2 = np.array(df_vacc_country["people_fully_vaccinated_per_hundred"])

    df_vacc_new = pd.DataFrame(np.transpose([vacc1, vacc2]))
    df_vacc_new.index = date
    df_vacc_new.columns = ["% vaccinated with 1 dose", "% fully vaccinated"]

    return df_vacc_new


def import_epidem_data():
    """ Recupera dati epidemiologici dal JHU CSSE
        (Johns Hopkins Unversity)"""

    base = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"  # noqa: E501
    file_confirmed = base + "time_series_covid19_confirmed_global.csv"
    file_deaths = base + "time_series_covid19_deaths_global.csv"
    file_recovered = base + "time_series_covid19_recovered_global.csv"
    return pd.read_csv(file_confirmed), pd.read_csv(file_deaths), pd.read_csv(file_recovered)


def get_epidemic_data(country, df_confirmed, df_deaths, df_recovered):
    """ Recupera dati epidemiologia per paese """
    ydata_cases = (df_confirmed[df_confirmed["Country/Region"] == country].iloc[:, 4:]).sum()
    ydata_deaths = (df_deaths[df_deaths["Country/Region"] == country].iloc[:, 4:]).sum()
    ydata_rec = (df_recovered[df_recovered["Country/Region"] == country].iloc[:, 4:]).sum()
    ydata_inf = ydata_cases-ydata_deaths-ydata_rec
    daily_cases = ydata_cases.diff().rolling(window=7).mean()
    daily_deaths = ydata_deaths.diff().rolling(window=7).mean()
    df_epidemic = pd.DataFrame(np.transpose([ydata_cases,
                                             ydata_inf,
                                             ydata_deaths,
                                             ydata_rec,
                                             daily_cases,
                                             daily_deaths]))
    df_epidemic.index = pd.to_datetime(df_confirmed.columns[4:])
    df_epidemic.columns = ["Total cases",
                           "Active infected",
                           "Total deaths",
                           "Total recovered",
                           "Daily cases (avg 7 days)",
                           "Daily deaths (avg 7 days)"]
    return df_epidemic


def get_vaccine_data_last(country, time_window=30, t0=-1, fully=True, last_day=False):
    """ Recupera dati sulla frazione di vaccinati
        medi negli ultimi 30 giorni """

    df_vacc_country = df_vacc[df_vacc["location"] == country].iloc[2:, :]
    vacc_fully = np.array(df_vacc_country["people_fully_vaccinated_per_hundred"
                                          if fully else
                                          "total_vaccinated_per_hundred"])
    vacc_ultimi_Ngiorni = np.mean(vacc_fully[t0-(time_window+1):t0
                                             if last_day
                                             else -1])
    return vacc_ultimi_Ngiorni


def get_deaths(country, time_window=30, t0=-1):
    """ Recupera decessi per la finestra temporale selezionata """
    decessi = np.array(df_deaths[df_deaths["Country/Region"] == country].iloc[:, 4:].sum())
    decessi_ultimi_Ngiorni = decessi[t0] - decessi[t0-(time_window+1)]
    return decessi_ultimi_Ngiorni


def compute_vaccini_decessi_eu(tw, fully=True, last_day=False):
    """ calcola vaccini e decessi nei 27 Paesi europei """

    dec_res_2021 = []
    vacc_res_2021 = []
    t0 = -1
    for p, abitanti in paesi_abitanti_eu.items():
        vacc_res_2021.append(get_vaccine_data_last(p,
                                                   time_window=tw,
                                                   fully=fully,
                                                   last_day=last_day))
        dec_res_2021.append(get_deaths(p, time_window=tw, t0=t0)/abitanti)
    dec_res_2021 = np.array(dec_res_2021)
    return vacc_res_2021, dec_res_2021


def linear_model(x, coeff_fit):
    y = coeff_fit[1] + coeff_fit[0]*x
    return y


def linear_fit(vacc_res_2021, dec_res_2021):
    """ fit lineare """

    coeff_fit = np.polyfit(vacc_res_2021, dec_res_2021, 1)
    x_grid = np.arange(0, 100, 1)
    y_grid = [linear_model(v, coeff_fit) for v in x_grid]

    # calcola R2 score
    y_pred = [linear_model(v, coeff_fit) for v in vacc_res_2021]
    y_test = dec_res_2021

    score = round(r2_score(y_test, y_pred), 2)
    print('R2 score è pari a', score)

    return x_grid, y_grid, score


def corr_window(tw):
    """ Recupera dati decessi e vaccini per la finestra
        temporale e i paesi selezionati """

    dec_res = []
    vacc_res = []
    for p, abitanti in paesi_abitanti_eu.items():
        vacc_res.append(get_vaccine_data_last(p, fully=True, last_day=True))
        dec_res.append(get_deaths(p, time_window=tw)/abitanti)
    corr_tw = np.corrcoef(vacc_res, dec_res)[0, 1]
    return corr_tw


def compute_max_correlation():
    """ calcola la finestra temporale in cui si ottiene
        la massima correlazione """

    tw_grid = np.arange(7, 300, 5)
    corr_grid = [corr_window(tw) for tw in tw_grid]
    ideal_window = tw_grid[np.argmin(corr_grid)]
    return ideal_window


# Rappresentazione grafica risultati
def plot_selection(show=False):
    """ Plot dati epidemiologia e vaccini dei paesi selezionati """

    # nota: nomi in Inglese
    nomi_nazioni = ["Italy", "Romania", "Portugal", "Spain", "Bulgaria"]

    label_nazioni = ["Italia", "Romania", "Portogallo", "Spagna", "Bulgaria"]
    abitanti_nazioni = [59.55, 19.29, 10.31, 47.35, 6.927]

    x_date = ["2021-07-01", "2021-08-01", "2021-09-01", "2021-10-01", "2021-11-01"]
    x_label = ["Lug\n2021", "Ago", "Set", "Ott", "Nov"]

    fig, axes2 = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))

    # Unpack all the axes subplots
    axes = axes2.ravel()

    last_updated = pd.to_datetime(x_date[-1])

    for i in range(len(nomi_nazioni)):
        df_epid = get_epidemic_data(nomi_nazioni[i],
                                    df_confirmed,
                                    df_deaths,
                                    df_recovered)
        new_date = df_epid.index[-1]
        mask_ = df_epid.index >= "2021-06-01"
        values = 7/(abitanti_nazioni[i]*10)*df_epid["Daily cases (avg 7 days)"]
        values[mask_].plot(ax=axes[0], label=label_nazioni[i], linewidth=2)
        last_updated, x_date, x_label = aggiorna_ascissa(last_updated,
                                                         new_date,
                                                         x_date,
                                                         x_label)

    axes[0].set_xlim("2021-06-01", last_updated)
    axes[0].set_title("Incidenza settimanale nuovi casi")
    axes[0].set_ylabel("Numeri ogni 100.000 abitanti")
    axes[0].set_xlabel("")
    axes[0].set_xticks(x_date)
    axes[0].set_xticklabels(x_label)
    axes[0].legend()
    axes[0].grid()
    axes[0].minorticks_off()

    for i in range(len(nomi_nazioni)):
        df_country = get_vaccine_data(nomi_nazioni[i], df_vacc)
        new_date = df_country.index[-1]
        mask_ = df_country.index >= "2021-06-01"
        df_country["% fully vaccinated"][mask_].plot(ax=axes[1],
                                                     label=label_nazioni[i],
                                                     linewidth=2)
        last_updated, x_date, x_label = aggiorna_ascissa(last_updated,
                                                         new_date,
                                                         x_date,
                                                         x_label)

    axes[1].set_xlim("2021-06-01", last_updated)
    axes[1].set_ylim(0, 100)
    axes[1].set_yticks(np.arange(0, 101, 20))
    axes[1].set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    axes[1].set_title("Vaccinati in modo completo")
    axes[1].set_xlabel("")
    axes[1].set_xticks(x_date)
    axes[1].set_xticklabels(x_label)
    axes[1].legend()
    axes[1].grid()
    axes[1].minorticks_off()

    # Add watermarks
    ax = plt.gca()
    add_watermark(fig, ax.xaxis.label.get_fontsize())

    plt.tight_layout()
    plt.savefig("../risultati/confronto_nazioni_epidemia-vaccino.png",
                dpi=300,
                bbox_inches="tight")
    if show:
        plt.show()


def plot_correlazione_vaccini_decessi(vacc_res_2021, dec_res_2021, x_grid, y_grid, window, score, show=False):
    """ scatter plot correlazione vaccini e decessi """

    fig = plt.figure(figsize=(15, 8))

    # scatter plot
    # genera lista di colori e dimensioni
    colors = plt.cm.nipy_spectral(np.linspace(0, 1, len(paesi_eu_ita)))
    sizes = 3*len(paesi_eu_ita)
    plt.scatter(vacc_res_2021, dec_res_2021, c=colors,
                edgecolor="black", linewidth=0.5, s=sizes)

    texts = [plt.text(vacc_res_2021[i],
             dec_res_2021[i],
             paesi_eu_ita[i],
             path_effects=[path_effects.Stroke(linewidth=0.075, foreground=colors[i])])
             for i in range(len(paesi_eu_ita))]

    # fix text overlap
    adjust_text(texts,
                expand_text=(1.15, 1.30),
                arrowprops=dict(arrowstyle="-", lw=1))

    # fit plot
    plt.plot(x_grid, y_grid, linestyle="--", label=f"Regressione lineare, R$^2$ score={score}")

    plt.ylim(-100, )
    plt.xlim(0, 100)
    title = "Frazione di vaccinati vs decessi nei 27 Paesi dell'UE"
    title += f" negli ultimi {window} giorni"
    title += f"\nCoefficiente di correlazione = {corr_coeff}"
    plt.title(title, fontsize=15)
    plt.xlabel(f"Frazione media di vaccinati con ciclo completo negli ultimi {window} giorni", fontsize=15)
    plt.ylabel("Decessi per milione di abitanti", fontsize=15)
    plt.xticks(np.arange(0, 101, 20), ["0%", "20%", "40%", "60%", "80%", "100%"])
    plt.grid()
    plt.legend(fontsize=15)

    # Add watermarks
    ax = plt.gca()
    add_watermark(fig, ax.xaxis.label.get_fontsize())

    plt.tight_layout()
    plt.savefig("../risultati/vaccini_decessi_EU.png",
                dpi=300,
                bbox_inches="tight")
    if show:
        plt.show()


if __name__ == "__main__":
    # Set work directory for the script
    scriptpath = path.dirname(path.realpath(__file__))
    chdir(scriptpath)

    # Set locale to "it" to parse the month correctly
    locale.setlocale(locale.LC_ALL, "it_IT.UTF-8")

    # Imposta stile grafici
    plt.style.use("seaborn-dark")

    # importa dati
    df_confirmed, df_deaths, df_recovered = import_epidem_data()
    df_vacc = import_vaccines_data()

    # plot dati selezione paesi
    plot_selection()

    # plot correlazione vaccini vs. decessi per paesi eu
    # calcola finestra temporale per cui si ottiene massima correlazione
    ideal_window = compute_max_correlation()
    window = 30  # giorni
    # recupera dati per tale finestra temporale
    vacc_res_2021, dec_res_2021 = compute_vaccini_decessi_eu(window, fully=True, last_day=False)
    x_grid, y_grid, score = linear_fit(vacc_res_2021, dec_res_2021)
    # calcola coefficiente di correlazione (pearson)
    corr_coeff = round(np.corrcoef(vacc_res_2021, dec_res_2021)[0, 1], 2)

    print("Coefficiente di correlazione tra vaccinati e deceduti:", corr_coeff)
    print("Finestra temporale in cui si registra la massima correlazione:",
          ideal_window,
          "giorni")

    plot_correlazione_vaccini_decessi(vacc_res_2021,
                                      dec_res_2021,
                                      x_grid,
                                      y_grid,
                                      window,
                                      score)
