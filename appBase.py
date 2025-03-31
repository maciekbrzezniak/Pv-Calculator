import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Nagłówek aplikacji
st.title("Kalkulator Opłacalności Fotowoltaiki z Magazynem Energii")

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
wzrost_cen_pradu = st.sidebar.slider("Wzrost cen prądu (% rocznie)", min_value=0, max_value=10, value=5) / 100
czas_eksploatacji = st.sidebar.slider("Czas eksploatacji instalacji (lata)", min_value=10, max_value=30, value=25)

# Parametry magazynu energii
st.sidebar.subheader("Magazyn energii")
uzycie_magazynu = st.sidebar.checkbox("Czy używasz magazynu energii?")
if uzycie_magazynu:
    pojemnosc_magazynu = st.sidebar.number_input("Pojemność magazynu (kWh)", min_value=5, max_value=50, value=10)
    sprawnosc_magazynu = st.sidebar.slider("Sprawność magazynu (%)", min_value=80, max_value=95, value=90) / 100
    koszt_magazynu = st.sidebar.number_input("Koszt magazynu (zł/kWh)", min_value=1500, max_value=5000, value=3000)
    dotacja_magazyn = st.sidebar.number_input("Dotacja na magazyn (zł)", min_value=0, max_value=20000, value=5000)
else:
    pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynu, dotacja_magazyn = 0, 1, 0, 0

# Obliczenia
roczne_zuzycie = zuzycie_miesieczne * 12
powierzchnia_panelu = 1.7  # Średnia powierzchnia jednego panelu [m²]
liczba_paneli = int(powierzchnia_dachu / powierzchnia_panelu)
moc_max = liczba_paneli * (moc_panelu / 1000)
moc_wymagana = roczne_zuzycie / (naslonecznienie * sprawnosc_paneli)
moc_instalacji = min(moc_max, moc_wymagana)
energia_produkcja = moc_instalacji * naslonecznienie * sprawnosc_paneli
koszt_instalacji = max(0, (moc_instalacji * cena_instalacji) - dotacja)
koszt_calosciowy = koszt_instalacji + max(0, (pojemnosc_magazynu * koszt_magazynu) - dotacja_magazyn)

# Obliczenie oszczędności
energia_dostepna = min(energia_produkcja, roczne_zuzycie)
oszczednosci_pierwszy_rok = energia_dostepna * cena_pradu
if oszczednosci_pierwszy_rok > 0:
    okres_zwrotu = koszt_calosciowy / oszczednosci_pierwszy_rok
else:
    okres_zwrotu = None

# Oszczędności w czasie
lata = np.arange(1, czas_eksploatacji + 1)
oszczednosci_lata = oszczednosci_pierwszy_rok * ((1 + wzrost_cen_pradu) ** lata)
oszczednosci_suma = np.cumsum(oszczednosci_lata)

# Wyświetlanie wyników
st.header("Wyniki kalkulacji")
st.write(f"🔋 **Moc instalacji:** {moc_instalacji:.2f} kWp")
st.write(f"⚡ **Roczna produkcja energii:** {energia_produkcja:.0f} kWh")
st.write(f"💰 **Koszt instalacji (po dotacji):** {koszt_instalacji:,.0f} zł")
st.write(f"🔋 **Koszt magazynu energii (po dotacji):** {max(0, (pojemnosc_magazynu * koszt_magazynu) - dotacja_magazyn):,.0f} zł")
st.write(f"📉 **Roczne oszczędności (pierwszy rok):** {oszczednosci_pierwszy_rok:,.0f} zł")

if okres_zwrotu and okres_zwrotu < czas_eksploatacji:
    st.write(f"⏳ **Okres zwrotu inwestycji:** {okres_zwrotu:.1f} lat")
else:
    st.write("⚠️ **Instalacja nie zwróci się w czasie eksploatacji!")

# Wykres oszczędności
st.subheader("Oszczędności na przestrzeni lat")
fig, ax = plt.subplots()
ax.plot(lata, oszczednosci_suma, label="Łączne oszczędności", color="green")
ax.axhline(y=koszt_calosciowy, color="red", linestyle="--", label="Koszt całkowity")
ax.set_xlabel("Lata")
ax.set_ylabel("Oszczędności (zł)")
ax.set_title("Przewidywane oszczędności w czasie")
ax.legend()
st.pyplot(fig)

# Podsumowanie
st.subheader("Podsumowanie")
if moc_instalacji < moc_wymagana:
    st.warning("⚠️ Instalacja nie pokryje całego zapotrzebowania na energię.")
elif moc_instalacji == moc_wymagana:
    st.success("✅ Instalacja pokryje pełne zapotrzebowanie na energię!")
else:
    st.info("💡 Instalacja może produkować nadwyżkę energii.")
