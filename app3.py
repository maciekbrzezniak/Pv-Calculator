import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Nagłówek aplikacji
st.title("Kalkulator Opłacalności Fotowoltaiki z Magazynem Energii i Pompą Ciepła")

# Sekcja wejściowa – parametry użytkownika
st.sidebar.header("Dane wejściowe")

# Wprowadzenie danych
zuzycie_miesieczne = st.sidebar.number_input(
    "Średnie miesięczne zużycie energii (kWh)",
    min_value=100, max_value=5000, value=300
)
cena_pradu = st.sidebar.number_input(
    "Cena prądu (zł/kWh)",
    min_value=0.1, max_value=2.0, value=0.8, step=0.01
)
powierzchnia_dachu = st.sidebar.number_input(
    "Dostępna powierzchnia dachu (m²)",
    min_value=5, max_value=100, value=30
)
naslonecznienie = st.sidebar.number_input(
    "Nasłonecznienie w regionie (kWh/m²/rok)",
    min_value=800, max_value=1500, value=1100
)
sprawnosc_paneli = st.sidebar.slider(
    "Sprawność paneli (%)", min_value=15, max_value=22, value=20
) / 100
moc_panelu = st.sidebar.number_input(
    "Moc pojedynczego panelu (Wp)",
    min_value=200, max_value=600, value=400
)
cena_instalacji = st.sidebar.number_input(
    "Koszt instalacji (zł/kWp)",
    min_value=3000, max_value=8000, value=4500
)
dotacja = st.sidebar.number_input(
    "Dotacja na instalację (zł)",
    min_value=0, max_value=20000, value=5000
)
wzrost_cen_pradu = st.sidebar.slider(
    "Wzrost cen prądu (% rocznie)", min_value=0, max_value=10, value=5
) / 100
czas_eksploatacji = st.sidebar.slider(
    "Czas eksploatacji instalacji (lata)",
    min_value=10, max_value=30, value=25
)

# Parametry magazynu energii
st.sidebar.subheader("Magazyn energii")
uzycie_magazynu = st.sidebar.checkbox("Czy używasz magazynu energii?")
if uzycie_magazynu:
    pojemnosc_magazynu = st.sidebar.number_input(
        "Pojemność magazynu (kWh)",
        min_value=5, max_value=50, value=10
    )
    sprawnosc_magazynu = st.sidebar.slider(
        "Sprawność magazynu (%)", min_value=80, max_value=95, value=90
    ) / 100
    koszt_magazynu = st.sidebar.number_input(
        "Koszt magazynu (zł/kWh)",
        min_value=1500, max_value=5000, value=3000
    )
    dotacja_magazyn = st.sidebar.number_input(
        "Dotacja na magazyn (zł)",
        min_value=0, max_value=20000, value=5000
    )
else:
    pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynu, dotacja_magazyn = 0, 1, 0, 0

# Parametry pompy ciepła
st.sidebar.subheader("Pompa ciepła")
uzycie_pompy = st.sidebar.checkbox("Czy używasz pompy ciepła?")
if uzycie_pompy:
    zuzycie_pompa_rok = st.sidebar.number_input(
        "Roczne zużycie energii przez pompę ciepła (kWh)",
        min_value=500, max_value=10000, value=2000
    )
    koszt_pompy = st.sidebar.number_input(
        "Koszt pompy ciepła (zł)",
        min_value=3000, max_value=50000, value=20000
    )
    dotacja_pompy = st.sidebar.number_input(
        "Dotacja na pompę ciepła (zł)",
        min_value=0, max_value=30000, value=5000
    )
else:
    zuzycie_pompa_rok, koszt_pompy, dotacja_pompy = 0, 0, 0

# --- OBLICZENIA ---

# Roczne zużycie -> zużycie "gniazdek" + pompa ciepła
roczne_zuzycie = (zuzycie_miesieczne * 12) + zuzycie_pompa_rok

# Powierzchnia pojedynczego panelu (typowo 1.6 - 2.0 m²)
powierzchnia_panelu = 1.7

# Maksymalna liczba paneli, ograniczona przez dach
liczba_paneli = int(powierzchnia_dachu / powierzchnia_panelu)
# Moc maksymalna instalacji
moc_max = liczba_paneli * (moc_panelu / 1000)

# Moc wymagana, by pokryć roczne zużycie
moc_wymagana = roczne_zuzycie / (naslonecznienie * sprawnosc_paneli)

# Ostateczna moc instalacji
moc_instalacji = min(moc_max, moc_wymagana)

# Roczna produkcja energii
energia_produkcja = moc_instalacji * naslonecznienie * sprawnosc_paneli

# Koszt instalacji (po dotacji)
koszt_instalacji_netto = max(0, (moc_instalacji * cena_instalacji) - dotacja)

# Koszt magazynu (po dotacji)
koszt_magazynu_netto = max(0, (pojemnosc_magazynu * koszt_magazynu) - dotacja_magazyn)

# Koszt pompy ciepła (po dotacji)
koszt_pompy_netto = max(0, koszt_pompy - dotacja_pompy)

# Całkowity koszt inwestycji
koszt_calosciowy = koszt_instalacji_netto + koszt_magazynu_netto + koszt_pompy_netto

# Oszczędności w pierwszym roku (przy założeniu, że wyprodukowana energia pokrywa część zużycia)
energia_dostepna = min(energia_produkcja, roczne_zuzycie)
oszczednosci_pierwszy_rok = energia_dostepna * cena_pradu

# Okres zwrotu (pierwsza przybliżona metoda)
if oszczednosci_pierwszy_rok > 0:
    okres_zwrotu = koszt_calosciowy / oszczednosci_pierwszy_rok
else:
    okres_zwrotu = None

# Oszczędności w kolejnych latach (z uwzględnieniem wzrostu cen prądu)
lata = np.arange(1, czas_eksploatacji + 1)
oszczednosci_lata = oszczednosci_pierwszy_rok * ((1 + wzrost_cen_pradu) ** lata)
oszczednosci_suma = np.cumsum(oszczednosci_lata)

# --- WYNIKI ---

st.header("Wyniki kalkulacji")
st.write(f"🔋 **Moc instalacji (PV):** {moc_instalacji:.2f} kWp")
st.write(f"⚡ **Roczna produkcja energii:** {energia_produkcja:.0f} kWh")
st.write(f"💰 **Koszt instalacji PV (po dotacji):** {koszt_instalacji_netto:,.0f} zł")
st.write(f"🔋 **Koszt magazynu energii (po dotacji):** {koszt_magazynu_netto:,.0f} zł")
st.write(f"🌡️ **Koszt pompy ciepła (po dotacji):** {koszt_pompy_netto:,.0f} zł")
st.write(f"💵 **Łączny koszt inwestycji:** {koszt_calosciowy:,.0f} zł")
st.write(f"📉 **Roczne oszczędności (pierwszy rok):** {oszczednosci_pierwszy_rok:,.0f} zł")

if okres_zwrotu and okres_zwrotu < czas_eksploatacji:
    st.write(f"⏳ **Okres zwrotu inwestycji:** {okres_zwrotu:.1f} lat")
elif okres_zwrotu:
    st.write("⚠️ **Instalacja nie zwróci się w czasie eksploatacji!**")
else:
    st.write("⚠️ **Brak oszczędności w pierwszym roku.**")

# --- WYKRES 1: Przewidywane oszczędności w czasie (liniowy) ---

st.subheader("Przewidywane oszczędności w czasie")

fig_savings = go.Figure()

# Krzywa łącznych oszczędności
fig_savings.add_trace(go.Scatter(
    x=lata,
    y=oszczednosci_suma,
    mode='lines',
    name='Łączne oszczędności',
    line=dict(width=3, color='green')
))

# Koszt całkowity jako linia przerywana
fig_savings.add_hline(
    y=koszt_calosciowy,
    line=dict(color='red', dash='dash'),
    annotation_text="Koszt całkowity",
    annotation_position="top left"
)

fig_savings.update_layout(
    title="Przewidywane oszczędności w czasie",
    xaxis_title="Lata",
    yaxis_title="Oszczędności (zł)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

st.plotly_chart(fig_savings, use_container_width=True)

# --- WYKRES 2: Zużycie vs. Produkcja energii (kolumny) ---

st.subheader("Porównanie zużycia i produkcji energii (rocznie)")

fig_usage = go.Figure(data=[
    go.Bar(
        name='Roczne zużycie',
        x=['Energia (kWh)'],
        y=[roczne_zuzycie],
        marker_color='blue'
    ),
    go.Bar(
        name='Roczna produkcja',
        x=['Energia (kWh)'],
        y=[energia_produkcja],
        marker_color='green'
    )
])

fig_usage.update_layout(
    barmode='group',
    title="Zużycie vs. Produkcja energii w skali roku",
    xaxis_title="Rodzaj",
    yaxis_title="kWh"
)

st.plotly_chart(fig_usage, use_container_width=True)

# --- PODSUMOWANIE ---

st.subheader("Podsumowanie")

if moc_instalacji < moc_wymagana:
    st.warning("⚠️ Instalacja nie pokryje całego zapotrzebowania na energię.")
elif abs(moc_instalacji - moc_wymagana) < 0.01:
    st.success("✅ Instalacja pokryje pełne zapotrzebowanie na energię!")
else:
    st.info("💡 Instalacja może produkować nadwyżkę energii.")
