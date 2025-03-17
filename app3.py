import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Nagłówek aplikacji
st.title("Kalkulator Opłacalności Fotowoltaiki z Magazynem Energii i Pompą Cieplną")

# Sekcja wejściowa – parametry użytkownika
st.sidebar.header("Dane wejściowe")

# Wprowadzenie danych
zuzycie_miesieczne = st.sidebar.number_input("Średnie miesięczne zużycie energii (kWh)", min_value=100, max_value=5000, value=300)
cena_pradu = st.sidebar.number_input("Cena prądu (zł/kWh)", min_value=0.1, max_value=2.0, value=0.8, step=0.01)
powierzchnia_dachu = st.sidebar.number_input("Dostępna powierzchnia dachu (m²)", min_value=5, max_value=100, value=30)
naslonecznienie = st.sidebar.number_input("Nasłonecznienie w regionie (kWh/m²/rok)", min_value=800, max_value=1500, value=1100)
sprawnosc_paneli = st.sidebar.slider("Sprawność paneli (%)", min_value=15, max_value=22, value=20) / 100
moc_panelu = st.sidebar.number_input("Moc pojedynczego panelu (Wp)", min_value=200, max_value=600, value=400)
cena_instalacji = st.sidebar.number_input("Koszt instalacji (zł/kWp)", min_value=3000, max_value=8000, value=4500)
dotacja = st.sidebar.number_input("Dotacja na instalację (zł)", min_value=0, max_value=20000, value=5000)

# Parametry magazynu energii
st.sidebar.header("Magazyn Energii")
magazyn_energii = st.sidebar.checkbox("Czy posiadasz magazyn energii?")
if magazyn_energii:
    pojemnosc_magazynu = st.sidebar.number_input("Pojemność magazynu energii (kWh)", min_value=2, max_value=20, value=10)
    sprawnosc_magazynu = st.sidebar.slider("Sprawność magazynu (%)", min_value=70, max_value=95, value=90) / 100
    koszt_magazynu = st.sidebar.number_input("Koszt magazynu energii (zł)", min_value=5000, max_value=50000, value=20000)

# Parametry pompy ciepłej
st.sidebar.header("Pompa Cieplna")
pompa_cieplna = st.sidebar.checkbox("Czy posiadasz pompę ciepła?")
if pompa_cieplna:
    moc_pompy = st.sidebar.number_input("Moc pompy cieplnej (kW)", min_value=3, max_value=20, value=10)
    cop_pompy = st.sidebar.number_input("Współczynnik COP pompy", min_value=2.0, max_value=5.0, value=3.5, step=0.1)
    koszt_pompy = st.sidebar.number_input("Koszt zakupu i montażu pompy (zł)", min_value=5000, max_value=50000, value=20000)

# Obliczenia produkcji energii
liczba_paneli = int(powierzchnia_dachu // 1.6)
roczna_produkcja = liczba_paneli * moc_panelu * sprawnosc_paneli * naslonecznienie / 1000

# Obliczenia zużycia energii przez pompę
if pompa_cieplna:
    zuzycie_pompy = (moc_pompy * 12 * 30) / cop_pompy  # Praca przez 12h dziennie przez cały miesiąc
    zuzycie_miesieczne += zuzycie_pompy

# Obliczenia wpływu magazynu energii
if magazyn_energii:
    energia_magazynowana = min(roczna_produkcja * sprawnosc_magazynu, pojemnosc_magazynu * 365 / 12)
    oszczednosci_dzieki_magazynowi = energia_magazynowana * cena_pradu
else:
    oszczednosci_dzieki_magazynowi = 0

# Koszty energii
roczny_koszt_pradu = zuzycie_miesieczne * 12 * cena_pradu
oszczednosci = min(roczna_produkcja, zuzycie_miesieczne * 12) * cena_pradu + oszczednosci_dzieki_magazynowi
koszt_netto = max(0, roczny_koszt_pradu - oszczednosci)

# Wyniki
st.subheader("Wyniki kalkulacji")
st.write(f"Całkowita produkcja energii z PV rocznie: {roczna_produkcja:.2f} kWh")
st.write(f"Roczny koszt energii bez PV: {roczny_koszt_pradu:.2f} zł")
st.write(f"Oszczędności dzięki PV: {oszczednosci:.2f} zł")
st.write(f"Roczny koszt energii po uwzględnieniu PV: {koszt_netto:.2f} zł")

if magazyn_energii:
    st.write(f"Oszczędności dzięki magazynowi energii: {oszczednosci_dzieki_magazynowi:.2f} zł")
    st.write(f"Koszt magazynu energii: {koszt_magazynu} zł")

if pompa_cieplna:
    st.write(f"Dodatkowe zużycie energii przez pompę cieplną: {zuzycie_pompy:.2f} kWh miesięcznie")
    st.write(f"Koszt pompy cieplnej: {koszt_pompy} zł")

# Wykres porównawczy
fig, ax = plt.subplots()
labels = ["Bez PV", "Z PV + Magazyn"]
koszty = [roczny_koszt_pradu, koszt_netto]
ax.bar(labels, koszty, color=["red", "green"])
ax.set_ylabel("Koszt (zł)")
ax.set_title("Porównanie kosztów energii")
st.pyplot(fig)
