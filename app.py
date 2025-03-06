import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Nagłówek aplikacji
st.title("Kalkulator Opłacalności Fotowoltaiki")

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
dotacja = st.sidebar.number_input("Dotacja (zł)", min_value=0, max_value=20000, value=5000)
wzrost_cen_pradu = st.sidebar.slider("Wzrost cen prądu (% rocznie)", min_value=0, max_value=10, value=5) / 100
czas_eksploatacji = st.sidebar.slider("Czas eksploatacji instalacji (lata)", min_value=10, max_value=30, value=25)

# Obliczenia
roczne_zuzycie = zuzycie_miesieczne * 12
powierzchnia_panelu = 1.7  # Średnia powierzchnia jednego panelu [m²]

# Obliczenie maksymalnej mocy instalacji, ograniczonej przez dach
liczba_paneli = int(powierzchnia_dachu / powierzchnia_panelu)
moc_max = liczba_paneli * (moc_panelu / 1000)

# Obliczenie wymaganej mocy do pokrycia zapotrzebowania
moc_wymagana = roczne_zuzycie / (naslonecznienie * sprawnosc_paneli)

# Ostateczna moc instalacji
moc_instalacji = min(moc_max, moc_wymagana)

# Obliczenie rocznej produkcji energii
energia_produkcja = moc_instalacji * naslonecznienie * sprawnosc_paneli

# Koszt instalacji po dotacjach
koszt_instalacji = max(0, (moc_instalacji * cena_instalacji) - dotacja)

# Roczne oszczędności
oszczednosci_pierwszy_rok = min(energia_produkcja, roczne_zuzycie) * cena_pradu

# Okres zwrotu inwestycji (bez wzrostu cen prądu)
if oszczednosci_pierwszy_rok > 0:
    okres_zwrotu = koszt_instalacji / oszczednosci_pierwszy_rok
else:
    okres_zwrotu = None

# Obliczenie oszczędności w czasie (z uwzględnieniem wzrostu cen energii)
lata = np.arange(1, czas_eksploatacji + 1)
oszczednosci_lata = oszczednosci_pierwszy_rok * ((1 + wzrost_cen_pradu) ** lata)
oszczednosci_suma = np.cumsum(oszczednosci_lata)

# **Wyświetlanie wyników**
st.header("Wyniki kalkulacji")

st.write(f"🔋 **Moc instalacji:** {moc_instalacji:.2f} kWp")
st.write(f"⚡ **Roczna produkcja energii:** {energia_produkcja:.0f} kWh")
st.write(f"💰 **Koszt instalacji (po dotacji):** {koszt_instalacji:,.0f} zł")
st.write(f"📉 **Roczne oszczędności (pierwszy rok):** {oszczednosci_pierwszy_rok:,.0f} zł")

if okres_zwrotu and okres_zwrotu < czas_eksploatacji:
    st.write(f"⏳ **Okres zwrotu inwestycji:** {okres_zwrotu:.1f} lat")
else:
    st.write("⚠️ **Instalacja nie zwróci się w czasie eksploatacji!**")

# **Wykres oszczędności w czasie**
st.subheader("Oszczędności na przestrzeni lat")
fig, ax = plt.subplots()
ax.plot(lata, oszczednosci_suma, label="Łączne oszczędności", color="green")
ax.axhline(y=koszt_instalacji, color="red", linestyle="--", label="Koszt instalacji")
ax.set_xlabel("Lata")
ax.set_ylabel("Oszczędności (zł)")
ax.set_title("Przewidywane oszczędności w czasie")
ax.legend()
st.pyplot(fig)

# **Dodatkowe informacje**
st.subheader("Podsumowanie")
if moc_instalacji < moc_wymagana:
    st.warning("⚠️ Twoja instalacja nie pokryje całego zapotrzebowania na energię.")
elif moc_instalacji == moc_wymagana:
    st.success("✅ Twoja instalacja w pełni pokryje zapotrzebowanie na energię!")
else:
    st.info("💡 Twoja instalacja może produkować nadwyżkę energii.")

